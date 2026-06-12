from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict


class Size(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

@dataclass(frozen=True)
class GenerationParams:
    T: Tuple[int, int]
    I_set: Tuple[int, int]
    nr_ratio: float
    groups: Tuple[int, int]
    workers: Tuple[int, int, int]
    skill: Tuple[int, int]

@dataclass
class ExperimentConfig:
    size: Size
    seed: int
    params: Dict[Size, GenerationParams]
    output_dir: str = "instances"

    @property
    def current(self) -> GenerationParams:
        return self.params[self.size]

params_dict = {
    Size.SMALL: GenerationParams(
        T=(10, 12),
        I_set=(300, 400),
        nr_ratio=0.15,
        groups=(20, 30),
        workers=(6, 6, 5),
        skill=(4, 6)
    ),
    Size.MEDIUM: GenerationParams(
        T=(16, 18),
        I_set=(500, 600),
        nr_ratio=0.20,
        groups=(40, 60),
        workers=(6, 6, 5),
        skill=(6, 8)
    ),
    Size.LARGE: GenerationParams(
        T=(36, 48),
        I_set=(800, 1000),
        nr_ratio=0.25,
        groups=(70, 90),
        workers=(6, 6, 5),
        skill=(8, 10)
    ),
}

