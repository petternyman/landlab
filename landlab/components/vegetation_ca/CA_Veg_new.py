""" Landlab component that simulates inter-species plant competition.

VegCA component simulates inter-species spatial plant competition based
on input cumulative water stress (converted to plant live index) and
existing vegetation organization. 
Ref: Zhou et. al, WRR Vol. 49 (2013) Pg.2872-2895.

.. codeauthor:: Sai Nudurupati and Erkan Istanbulluoglu
"""
from landlab import Component
import numpy as np
from ...utils.decorators import use_file_name_or_kwds

_VALID_METHODS = set(['Grid'])
GRASS = 0
SHRUB = 1
TREE = 2
BARE = 3
SHRUBSEEDLING = 4
TREESEEDLING = 5

def assert_method_is_valid(method):
    if method not in _VALID_METHODS:
        raise ValueError('%s: Invalid method name' % method)


class VegCA(Component):
    """
    Landlab component that simulates inter-species plant competition using
    a 2D cellular automata model.
    
    Construction::
        VegCA(grid, Pemaxg=0.35, ING=2., ThetaGrass=0.62, PmbGrass=0.05,
            Pemaxsh=0.2, ThetaShrub=0.8, PmbShrub=0.01, tpmaxShrub=600,
            Pemaxtr=0.25, ThetaTree=0.72, PmbTree=0.01, tpmaxTree=350,
            ThetaShrubSeedling=0.64, PmbShrubSeedling=0.03,
            tpmaxShrubSeedling=18, ThetaTreeSeedling=0.64,
            PmbTreeSeedling=0.03, tpmaxTreeSeedling=18)
    
    Parameters
    ----------
    grid: RasterModelGrid
        A grid.
    Pemaxg: float, optional
        Maximal establishment probability of grass.
    ING: float, optional
        Parameter to define allelopathic effect of creosote on grass.
    ThetaGrass: float, optional
        Drought resistance threshold of grass.
    PmbGrass: float, optional
        Background mortality probability of grass.
    Pemaxsh: float, optional
        Maximal establishment probability of shrub.
    ThetaShrub: float, optional
        Drought resistance threshold of shrub.
    PmbShrub: float, optional
        Background mortality probability of shrub.
    tpmaxShrub: float, optional
        Maximum age of shrub (years).
    Pemaxtr: float, optional
        Maximal establishment probability of tree.
    Thetatree: float, optional
        Drought resistance threshold of tree.
    PmbTree: float, optional
        Background mortality probability of tree.
    tpmaxTree: float, optional
        Maximum age of tree (years).
    ThetaShrubSeedling: float, optional
        Drought resistance threshold of shrub seedling.
    PmbShrubSeedling: float, optional
        Background mortality probability of shrub seedling.
    tpmaxShrubSeedling: float, optional
        Maximum age of shrub seedling (years).
    ThetaTreeSeedling: float, optional
        Drought resistance threshold of tree seedling.
    PmbTreeSeedling: float, optional
        Background mortality probability of tree seedling.
    tpmaxTreeSeedling: float, optional
        Maximum age of tree seedling (years).
    """
    _name = 'VegCA'

    _input_var_names = (
        'soil_moisture__water_stress_cumulative',
        'vegetation__plant_functional_type',
    )

    _output_var_names = (
        'vegetation__live_leaf_area_index',
        'plant__age',
    )

    _var_units = {
        'soil_moisture__water_stress_cumulative': 'Pa',
        'vegetation__plant_functional_type': 'None',
        'vegetation__live_leaf_area_index': 'Pa',
        'plant__age': 'Years',
    }
    
    _var_mapping = {
        'soil_moisture__water_stress_cumulative': 'cell',
        'vegetation__plant_functional_type': 'cell',
        'vegetation__live_leaf_area_index': 'cell',
        'plant__age': 'cell',
    }
    
    _var_doc = {
        'soil_moisture__water_stress_cumulative':
            'cumulative soil_moisture__water_stress over the growing season',
        'vegetation__plant_functional_type':
            'classification of plants (int), grass=0, shrub=1, tree=2, \
             bare=3, shrub_seedling=4, tree_seedling=5',
        'vegetation__live_leaf_area_index':
            'one-sided green leaf area per unit ground surface area',
        'plant__age':
            'Age of plant (years)',
    }

    @use_file_name_or_kwds
    def __init__(self, grid,
            Pemaxg=0.35, ING=2., ThetaGrass=0.62, PmbGrass=0.05,
            Pemaxsh=0.2, ThetaShrub=0.8, PmbShrub=0.01, tpmaxShrub=600,
            Pemaxtr=0.25, ThetaTree=0.72, PmbTree=0.01, tpmaxTree=350,
            ThetaShrubSeedling=0.64, PmbShrubSeedling=0.03,
            tpmaxShrubSeedling=18, ThetaTreeSeedling=0.64,
            PmbTreeSeedling=0.03, tpmaxTreeSeedling=18,
            **kwds):
        """
        Parameters
        ----------
        grid: RasterModelGrid
            A grid.
        Pemaxg: float, optional
            Maximal establishment probability of grass.
        ING: float, optional
            Parameter to define allelopathic effect of creosote on grass.
        ThetaGrass: float, optional
            Drought resistance threshold of grass.
        PmbGrass: float, optional
            Background mortality probability of grass.
        Pemaxsh: float, optional
            Maximal establishment probability of shrub.
        ThetaShrub: float, optional
            Drought resistance threshold of shrub.
        PmbShrub: float, optional
            Background mortality probability of shrub.
        tpmaxShrub: float, optional
            Maximum age of shrub (years).
        Pemaxtr: float, optional
            Maximal establishment probability of tree.
        Thetatree: float, optional
            Drought resistance threshold of tree.
        PmbTree: float, optional
            Background mortality probability of tree.
        tpmaxTree: float, optional
            Maximum age of tree (years).
        ThetaShrubSeedling: float, optional
            Drought resistance threshold of shrub seedling.
        PmbShrubSeedling: float, optional
            Background mortality probability of shrub seedling.
        tpmaxShrubSeedling: float, optional
            Maximum age of shrub seedling (years).
        ThetaTreeSeedling: float, optional
            Drought resistance threshold of tree seedling.
        PmbTreeSeedling: float, optional
            Background mortality probability of tree seedling.
        tpmaxTreeSeedling: float, optional
            Maximum age of tree seedling (years).        
        """
        self._method = kwds.pop('method', 'Grid')
        self._Pemaxg = Pemaxg   # Pe-max-grass - max probability
        self._Pemaxsh = Pemaxsh    # Pe-max-shrub
        self._Pemaxtr = Pemaxtr   # Pe-max-tree
        self._INg = ING  # Allelopathic effect on grass from creosotebush
        self._th_g = ThetaGrass  # grass
        self._th_sh = ThetaShrub # shrub - Creosote
        self._th_tr = ThetaTree # Juniper pine
        self._th_sh_s = ThetaShrubSeedling # shrub seedling
        self._th_tr_s = ThetaTreeSeedling # Juniper pine seedling
        self._Pmb_g = PmbGrass # Background mortality probability - grass
        self._Pmb_sh = PmbShrub # shrub
        self._Pmb_tr = PmbTree # tree
        self._Pmb_sh_s = PmbShrubSeedling # shrub seedling
        self._Pmb_tr_s = PmbTreeSeedling # tree seedling
        self._tpmax_sh = tpmaxShrub # Maximum age - shrub
        self._tpmax_tr = tpmaxTree # Maximum age - tree
        self._tpmax_sh_s = tpmaxShrubSeedling # Maximum age - shrub seedling
        self._tpmax_tr_s = tpmaxTreeSeedling # Maximum age - tree seedling


        assert_method_is_valid(self._method)

        super(VegCA, self).__init__(grid, **kwds)

        for name in self._input_var_names:
            if name not in self.grid.at_cell:
                self.grid.add_zeros('cell', name, units=self._var_units[name])

        for name in self._output_var_names:
            if name not in self.grid.at_cell:
                self.grid.add_zeros('cell', name, units=self._var_units[name])

        self._cell_values = self.grid['cell']

        if (np.all(grid['cell']['vegetation__plant_functional_type']) == 0):
            grid['cell']['vegetation__plant_functional_type'] =              \
                    np.random.randint(0,6,grid.number_of_cells)

        VegType = grid['cell']['vegetation__plant_functional_type']
        tp = np.zeros(grid.number_of_cells, dtype = int)
        tp[VegType == TREE] = np.random.randint(0,self._tpmax_tr,
                                    np.where(VegType==TREE)[0].shape)
        tp[VegType == SHRUB] = np.random.randint(0,self._tpmax_sh,
                                    np.where(VegType==SHRUB)[0].shape)
        VegType[tp[VegType == TREE] < self._tpmax_tr_s] = TREESEEDLING
        VegType[tp[VegType == SHRUB] < self._tpmax_sh_s] = SHRUBSEEDLING
        grid['cell']['plant__age'] = tp


    def update(self, time_elapsed = 1, Edit_VegCov = True):
        """
        Update fields with current loading conditions.

        Parameters
        ----------
        time_elapsed: int, optional
            Time elapsed - time step (years).
        Edit_VegCov: switch (0 or 1), optional
            If Edit_VegCov=1, an optional field 'vegetation__boolean_vegetated'
            will be output, (i.e.) if a cell is vegetated the corresponding
            cell of the field will be 1, otherwise it will be 0.
        """
        self._VegType = \
            self._cell_values['vegetation__plant_functional_type']
        self._CumWS   = \
            self._cell_values['soil_moisture__water_stress_cumulative']
        self._live_index = \
            self._cell_values['vegetation__live_leaf_area_index']
        self._tp = self._cell_values['plant__age'] + time_elapsed

        # Check if shrub and tree seedlings have matured
        shrub_seedlings = np.where(self._VegType == SHRUBSEEDLING)[0]
        tree_seedlings = np.where(self._VegType == TREESEEDLING)[0]
        matured_shrubs = np.where(self._tp[shrub_seedlings] >
                                    self._tpmax_sh_s)[0]
        matured_trees = np.where(self._tp[tree_seedlings] >
                                    self._tpmax_tr_s)[0]
        self._VegType[shrub_seedlings[matured_shrubs]] = SHRUB
        self._VegType[tree_seedlings[matured_trees]] = TREE
        self._tp[shrub_seedlings[matured_shrubs]] = 0
        self._tp[tree_seedlings[matured_trees]] = 0

        # Establishment
        self._live_index = 1 - self._CumWS      # Plant live index = 1 - WS
        bare_cells = np.where(self._VegType == BARE)[0]
        n_bare = len(bare_cells)
        first_ring = self.grid.get_looped_cell_neighbor_list(bare_cells)
        second_ring =                                                   \
            self.grid.get_second_ring_looped_cell_neighbor_list(bare_cells)
        veg_type_fr = self._VegType[first_ring]
        veg_type_sr = self._VegType[second_ring]
        Sh_WS_fr = WS_PFT( veg_type_fr, SHRUB, self._live_index[first_ring] )
        Tr_WS_fr = WS_PFT( veg_type_fr, TREE, self._live_index[first_ring] )
        Tr_WS_sr = WS_PFT( veg_type_sr, TREE, self._live_index[second_ring] )

        n = count(veg_type_fr, SHRUB)
        Phi_sh = Sh_WS_fr/8.
        Phi_tr = (Tr_WS_fr + Tr_WS_sr/2.)/8.
        Phi_g = np.mean(self._live_index[np.where(self._VegType == GRASS)])
        Pemaxg = self._Pemaxg * np.ones(n_bare)
        Pemaxsh = self._Pemaxsh * np.ones(n_bare)
        Pemaxtr = self._Pemaxtr * np.ones(n_bare)
        Peg = np.amin(np.vstack((Phi_g/(n*self._INg),Pemaxg)),axis = 0)
        Pesh = np.amin(np.vstack((Phi_sh, Pemaxsh)), axis = 0)
        Petr = np.amin(np.vstack((Phi_tr, Pemaxtr)), axis = 0)
        Select_PFT_E = np.random.choice([GRASS, SHRUBSEEDLING, TREESEEDLING],
                                        n_bare)
        # Grass - 0; Shrub Seedling - 4; Tree Seedling - 5
        Pest = np.choose(Select_PFT_E, [Peg, 0, 0, 0, Pesh, Petr])
        # Probability of establishment
        R_Est = np.random.rand(n_bare)
        # Random number for comparison to establish
        Establish = np.int32(np.where(np.greater_equal(Pest, R_Est)==True)[0])
        self._VegType[bare_cells[Establish]] = Select_PFT_E[Establish]
        self._tp[bare_cells[Establish]] = 0

        # Mortality
        plant_cells = np.where(self._VegType != BARE)[0]
        n_plant = len(plant_cells)
        Theta = np.choose(self._VegType[plant_cells],
                    [ self._th_g, self._th_sh, self._th_tr,
                            0, self._th_sh_s, self._th_tr_s])
        PMd = self._CumWS[plant_cells] - Theta
        PMd[PMd < 0.] = 0.
        tpmax = np.choose(self._VegType[plant_cells],
                    [ 200000, self._tpmax_sh, self._tpmax_tr,
                            0, self._tpmax_sh_s, self._tpmax_tr_s])
        PMa = np.zeros(n_plant)
        tp_plant = self._tp[plant_cells]
        tp_greater = np.where(tp_plant>0.5*tpmax)[0]
        PMa[tp_greater] = ((tp_plant[tp_greater] - 0.5 * tpmax[tp_greater]) /
                           (0.5 * tpmax[tp_greater])) - 1
        PMb = np.choose( self._VegType[plant_cells],
                            [self._Pmb_g, self._Pmb_sh, self._Pmb_tr, 0,
                                self._Pmb_sh_s, self._Pmb_tr_s] )
        PM = PMd + PMa + PMb
        PM[PM>1.] = 1.
        R_Mor = np.random.rand(n_plant) # Random number for comparison to kill
        Mortality = np.int32(np.where(np.greater_equal(PM, R_Mor) == True)[0])
        self._VegType[plant_cells[Mortality]] = BARE
        self._tp[plant_cells[Mortality]] = 0

        self._cell_values['plant__age'] = self._tp

        if Edit_VegCov:
            self.grid['cell']['vegetation__boolean_vegetated'] =             \
                        np.zeros(self.grid.number_of_cells, dtype=int)
            self.grid['cell']['vegetation__boolean_vegetated'][
                        self._VegType != BARE] = 1

        # For debugging purposes
        self._bare_cells = bare_cells
        self._Established = bare_cells[Establish]
        self._plant_cells = plant_cells
        self._Mortified = plant_cells[Mortality]



def count( Arr, value ):
    Res = np.zeros(Arr.shape[0],dtype = int)
    x,y = Arr.shape
    for i in range(0,x):
        for j in range(0,y):
            if Arr[i][j] == value:
                Res[i] += 1
    return Res


def WS_PFT( VegType, PlantType, WS ):
    Phi = np.zeros(WS.shape[0])
    x,y = WS.shape
    for i in range(0,x):
        for j in range(0,y):
            if VegType[i][j] == PlantType:
                Phi[i] += WS[i][j]
    return Phi
