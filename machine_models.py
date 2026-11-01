"""
Machine model definitions.

Every machine model the emulator can impersonate is described by one
MachineModel instance.  It carries the identification string the machine
answers the BELL command with and the feature set (memory areas, memory
cards) that drives both the UI and the protocol handlers.

This module is the single source of truth for model data - no other table of
model names, identification strings or feature flags should exist.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class MachineModel:
    """Feature set of one machine model."""

    name: str
    identification: str  # answer to the BELL command (without the CTRL_ETX)

    # P-Memory : internal pattern memory
    p_memory: bool
    p_memory_bytes: Optional[int] = None
    p_memory_slots: Optional[int] = None

    # M-Memory : stitch sequence memory
    m_memory: bool = True

    # Memory cards
    memory_cards: bool = False
    card_embroidery: bool = False  # Embroidery card space (small / large hoop)
    card_p_muster: bool = False    # P-Muster (9mm / MAXI) card spaces

    def __post_init__(self) -> None:
        if self.p_memory:
            if self.p_memory_bytes is None or self.p_memory_slots is None:
                raise ValueError(
                    f"{self.name}: p_memory requires p_memory_bytes and p_memory_slots"
                )
        elif self.p_memory_bytes is not None or self.p_memory_slots is not None:
            raise ValueError(
                f"{self.name}: p_memory is disabled but a size or slot count is set"
            )
        if (self.card_embroidery or self.card_p_muster) and not self.memory_cards:
            raise ValueError(
                f"{self.name}: card spaces require memory_cards"
            )


# Ordered registry: the first entry is the default model.
MACHINE_MODELS: Tuple[MachineModel, ...] = (
    MachineModel(
        name="PFAFF Creative 7570",
        identification="Copyright 1992 - 97       G.M. PFAFF AG Creative 7570B    Vers. 2.1",  # From real machine
        # Another firmware answers: "Copyright 1992 - 96       G.M. PFAFF AG Creative 7570D    Vers. 2.0"
        p_memory=True,
        p_memory_bytes=40710, # From real machine
        p_memory_slots=30,
        m_memory=True,
        memory_cards=True,
        card_embroidery=True,
        card_p_muster=True,
    ),
    MachineModel(
        name="PFAFF Creative 7560",
        identification="Copyright 1992 - 98       G.M. PFAFF AG      Creative 7560F    Vers. 1.0",  # From real machine
        p_memory=False,  # 7560 has no P-Memory
        p_memory_bytes=None,
        p_memory_slots=None,
        m_memory=True,
        memory_cards=True,
        card_embroidery=True,
        card_p_muster=False,
    ),
    MachineModel(
        name="PFAFF Creative 7550",
        identification="Copyright 1992,-93,-94    G.M. PFAFF AG Creative 7550 CD  Vers. 2.0",  # From real machine
        p_memory=True,
        p_memory_bytes=40710, # From real machine
        p_memory_slots=30,
        m_memory=True,
        memory_cards=False,
        card_embroidery=False,
        card_p_muster=False,
    ),
    MachineModel(
        name="PFAFF Creative 1475 CD",
        identification="Copyright 1990, 1991,     G.M. PFAFF AG      Creative 1475 CD  Vers. 4  ",  # From real machine
        p_memory=True,
        p_memory_bytes=6460, # From real machine
        p_memory_slots=16,
        m_memory=True,
        memory_cards=False,
        card_embroidery=False,
        card_p_muster=False,
    ),
    MachineModel(
        name="PFAFF Creative 1475A",
        identification="Copyright 1990, 1991, 1992,    G.M. PFAFF AG Creative 1475A    Vers. 1  ",  # From real machine
        p_memory=True,
        p_memory_bytes=6460,  # Guess, could actually be more
        p_memory_slots=16,
        m_memory=True,
        memory_cards=False,
        card_embroidery=False,
        card_p_muster=False,
    ),
)

MODELS_BY_NAME: Dict[str, MachineModel] = {model.name: model for model in MACHINE_MODELS}

DEFAULT_MODEL_NAME = MACHINE_MODELS[0].name


def get_model(name: str) -> MachineModel:
    """Return the MachineModel registered under *name*.

    Raises ValueError for an unknown model name.
    """
    try:
        return MODELS_BY_NAME[name]
    except KeyError:
        raise ValueError(f"Unknown model: {name}") from None
