"""Callable interfaces used by the RFC 8785 benchmark framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from .models import Dataset


InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')
OperationInputT = TypeVar('OperationInputT', contravariant=True)
OperationOutputT = TypeVar('OperationOutputT', covariant=True)
FactoryInputT = TypeVar('FactoryInputT', covariant=True)
FactoryOutputT = TypeVar('FactoryOutputT', covariant=True)
MeasurementOutputT = TypeVar('MeasurementOutputT', contravariant=True)


class ImplementationOperation(Protocol[OperationInputT, OperationOutputT]):
    """An implementation operation that transforms benchmark input into output."""

    def __call__(self, value: OperationInputT, /) -> OperationOutputT: ...


class InputFactory(Protocol[FactoryInputT]):
    """Build one benchmark input from a dataset."""

    def __call__(self, dataset: Dataset, /) -> FactoryInputT: ...


class ExpectedOutputFactory(Protocol[FactoryOutputT]):
    """Build the expected implementation output from a dataset."""

    def __call__(self, dataset: Dataset, /) -> FactoryOutputT: ...
