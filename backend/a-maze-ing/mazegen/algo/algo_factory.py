from .astar import AstarSolve
from .backtracking import BacktrackingGen
from .bfs import BfsSolve
from .binary_tree import BinaryTreeGen
from .dfs import DfsSolve
from .prim import PrimGen
from .sidewinder import SidewinderGen
from .utils import AlgorithmGen, AlgorithmSolve, GenerateMethod, SolveMethod


class AlgorithmFactory:
    '''
        Create an instance for a given Generator or Solve algorithm

        It has a registry of the different algorithm and can
        dynamically instanciate them

        Attributes:
            _registry: A dict that associate a generating/solving method
                       with it's class
    '''
    _registry: dict[
        GenerateMethod | SolveMethod, type[AlgorithmGen] | type[AlgorithmSolve]
    ] = {
        GenerateMethod.BACKTRACKING: BacktrackingGen,
        GenerateMethod.BINARY_TREE: BinaryTreeGen,
        GenerateMethod.PRIM: PrimGen,
        GenerateMethod.SIDEWINDER: SidewinderGen,
        SolveMethod.ASTAR: AstarSolve,
        SolveMethod.BFS: BfsSolve,
        SolveMethod.DFS: DfsSolve,
    }

    @classmethod
    def create(
        cls, method: GenerateMethod | SolveMethod, **kwargs
    ) -> AlgorithmGen | AlgorithmSolve:
        '''
            Create and Initialise an instance of the given algorithm

            Args:
                method: The choosen algorithm (solve or generate)
                **kwargs: keyword args given to the constructor of the
                          given algorithm

            Returns:
                An initialised instance of the given class

            Raise:
                ValueError: If the asked method is not in the registry
        '''
        algo = cls._registry.get(method)
        if not algo:
            raise ValueError("Update the AlgorithmFactory!")
        return algo(**kwargs)
