from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.field_200 import Field200
from ...models.field_401 import Field401
from ...models.field_404 import Field404
from ...models.field_429 import Field429
from ...types import Response


def _get_kwargs() -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/api/mapasygraficos/analisis",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Field200, Field401, Field404, Field429]]:
    if response.status_code == 200:
        response_200 = Field200.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = Field401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = Field404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = Field429.from_dict(response.json())

        return response_429
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Field200, Field401, Field404, Field429]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[Union[Field200, Field401, Field404, Field429]]:
    """Mapas de análisis. Última pasada.

     Estos mapas muestran la configuración de la presión en superficie usando isobaras (lineas de igual
    presión), áreas de alta (A, a) y baja (B, b) presión y los frentes en Europa y el Atlántico Norte.El
    mapa de análisis presenta el estado de la atmósfera a la hora correspondiente y los fenómenos más
    relevantes observados en España. Periodicidad de actualización: cada 12 horas (00, 12).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Field200, Field401, Field404, Field429]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Field200, Field401, Field404, Field429]]:
    """Mapas de análisis. Última pasada.

     Estos mapas muestran la configuración de la presión en superficie usando isobaras (lineas de igual
    presión), áreas de alta (A, a) y baja (B, b) presión y los frentes en Europa y el Atlántico Norte.El
    mapa de análisis presenta el estado de la atmósfera a la hora correspondiente y los fenómenos más
    relevantes observados en España. Periodicidad de actualización: cada 12 horas (00, 12).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Field200, Field401, Field404, Field429]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[Union[Field200, Field401, Field404, Field429]]:
    """Mapas de análisis. Última pasada.

     Estos mapas muestran la configuración de la presión en superficie usando isobaras (lineas de igual
    presión), áreas de alta (A, a) y baja (B, b) presión y los frentes en Europa y el Atlántico Norte.El
    mapa de análisis presenta el estado de la atmósfera a la hora correspondiente y los fenómenos más
    relevantes observados en España. Periodicidad de actualización: cada 12 horas (00, 12).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Field200, Field401, Field404, Field429]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Field200, Field401, Field404, Field429]]:
    """Mapas de análisis. Última pasada.

     Estos mapas muestran la configuración de la presión en superficie usando isobaras (lineas de igual
    presión), áreas de alta (A, a) y baja (B, b) presión y los frentes en Europa y el Atlántico Norte.El
    mapa de análisis presenta el estado de la atmósfera a la hora correspondiente y los fenómenos más
    relevantes observados en España. Periodicidad de actualización: cada 12 horas (00, 12).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Field200, Field401, Field404, Field429]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
