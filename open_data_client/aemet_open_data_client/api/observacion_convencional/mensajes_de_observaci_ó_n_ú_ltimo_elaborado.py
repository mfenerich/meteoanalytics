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


def _get_kwargs(
    tipomensaje: str,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/observacion/convencional/mensajes/tipomensaje/{tipomensaje}",
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
    tipomensaje: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Field200, Field401, Field404, Field429]]:
    """Mensajes de observación. Último elaborado.

     Últimos mensajes de observación. Para los SYNOP y TEMP devuelve los mensajes de las últimas 24 horas
    y para los CLIMAT de los 40 últimos dias. Se pasa como parámetro el tipo de mensaje que se desea
    (tipomensaje). El resultado de la petición es un fichero en formato tar.gz, que contiene los
    boletines en formato json y bufr.<br><br> <a
    href='https://opendata.aemet.es/centrodedescargas/rssatom'
        target='_blank'>Canales RSS</a> disponibles:
            <ul>
            <li>Observación convencional mensajes: climat</li>
            <li>Observación convencional mensajes: synop</li>
            <li>Observación convencional mensajes: temp</li>
            <li>Observación convencional mensajes: todos</li>
            </ul>

    Args:
        tipomensaje (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Field200, Field401, Field404, Field429]]
    """

    kwargs = _get_kwargs(
        tipomensaje=tipomensaje,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tipomensaje: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Field200, Field401, Field404, Field429]]:
    """Mensajes de observación. Último elaborado.

     Últimos mensajes de observación. Para los SYNOP y TEMP devuelve los mensajes de las últimas 24 horas
    y para los CLIMAT de los 40 últimos dias. Se pasa como parámetro el tipo de mensaje que se desea
    (tipomensaje). El resultado de la petición es un fichero en formato tar.gz, que contiene los
    boletines en formato json y bufr.<br><br> <a
    href='https://opendata.aemet.es/centrodedescargas/rssatom'
        target='_blank'>Canales RSS</a> disponibles:
            <ul>
            <li>Observación convencional mensajes: climat</li>
            <li>Observación convencional mensajes: synop</li>
            <li>Observación convencional mensajes: temp</li>
            <li>Observación convencional mensajes: todos</li>
            </ul>

    Args:
        tipomensaje (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Field200, Field401, Field404, Field429]
    """

    return sync_detailed(
        tipomensaje=tipomensaje,
        client=client,
    ).parsed


async def asyncio_detailed(
    tipomensaje: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Field200, Field401, Field404, Field429]]:
    """Mensajes de observación. Último elaborado.

     Últimos mensajes de observación. Para los SYNOP y TEMP devuelve los mensajes de las últimas 24 horas
    y para los CLIMAT de los 40 últimos dias. Se pasa como parámetro el tipo de mensaje que se desea
    (tipomensaje). El resultado de la petición es un fichero en formato tar.gz, que contiene los
    boletines en formato json y bufr.<br><br> <a
    href='https://opendata.aemet.es/centrodedescargas/rssatom'
        target='_blank'>Canales RSS</a> disponibles:
            <ul>
            <li>Observación convencional mensajes: climat</li>
            <li>Observación convencional mensajes: synop</li>
            <li>Observación convencional mensajes: temp</li>
            <li>Observación convencional mensajes: todos</li>
            </ul>

    Args:
        tipomensaje (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Field200, Field401, Field404, Field429]]
    """

    kwargs = _get_kwargs(
        tipomensaje=tipomensaje,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tipomensaje: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Field200, Field401, Field404, Field429]]:
    """Mensajes de observación. Último elaborado.

     Últimos mensajes de observación. Para los SYNOP y TEMP devuelve los mensajes de las últimas 24 horas
    y para los CLIMAT de los 40 últimos dias. Se pasa como parámetro el tipo de mensaje que se desea
    (tipomensaje). El resultado de la petición es un fichero en formato tar.gz, que contiene los
    boletines en formato json y bufr.<br><br> <a
    href='https://opendata.aemet.es/centrodedescargas/rssatom'
        target='_blank'>Canales RSS</a> disponibles:
            <ul>
            <li>Observación convencional mensajes: climat</li>
            <li>Observación convencional mensajes: synop</li>
            <li>Observación convencional mensajes: temp</li>
            <li>Observación convencional mensajes: todos</li>
            </ul>

    Args:
        tipomensaje (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Field200, Field401, Field404, Field429]
    """

    return (
        await asyncio_detailed(
            tipomensaje=tipomensaje,
            client=client,
        )
    ).parsed
