from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Field429")


@_attrs_define
class Field429:
    """
    Attributes:
        descripcion (str):  Default: 'Too Many Requests'.
        estado (int):
    """

    estado: int
    descripcion: str = "Too Many Requests"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        descripcion = self.descripcion

        estado = self.estado

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "descripcion": descripcion,
                "estado": estado,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        descripcion = d.pop("descripcion")

        estado = d.pop("estado")

        field_429 = cls(
            descripcion=descripcion,
            estado=estado,
        )

        field_429.additional_properties = d
        return field_429

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
