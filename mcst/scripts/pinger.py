import typing as t

import asyncio

from pprint import pp
from warnings import warn

from sqlalchemy import select
from sqlalchemy.orm import Session
from mcstatus import JavaServer, BedrockServer

from mcst.database.engine import ENGINE
from mcst.database.models import Server, Player, Record
from mcst.database.validation import is_valid_username



async def ping_server(ip_port: str, server_type: str='java') -> t.Optional[dict[str, t.Any]]:
    """
        Pings a server. Returns the server record corresponding to the server.

        If failed, returns `None` instead.
    """

    host, port = ip_port.split(':', maxsplit=1)

    if server_type == 'java':
        server = JavaServer(host=host, port=int(port))


        try:
            result = await server.async_status()

        except Exception:
            return None

        try:
            query = await server.async_query()
        except Exception:
            query = None

        if result.players.max == 0 or (query is not None and query.players.max == 0):
            warn(f"Skipping `ip_port`, max. player count is 0, which means that it is offline")

        return dict(
            query=query is not None,

            max_players=query.players.max if query is not None else result.players.max,
            online_players=query.players.online if query is not None else result.players.online,

            motd=query.motd if query is not None else result.description,
            latency=result.latency,

            version=query.software.version if query is not None else result.version.name,
            version_brand=query.software.brand if query is not None else None,

            map_name=query.map if query is not None else None,
            gamemode=None,
            icon=result.favicon,
            plugins=query.software.plugins if query is not None else None,

            server_id=ip_port,
            players=[Player(uuid=player.id, username=player.name) for player in (result.players.sample or []) if is_valid_username(player.name)]
        )


    elif server_type == 'bedrock':
        server = BedrockServer(host=host, port=int(port))
        return None # not implemented yet


    else:
        warn(f"Unsupported server type: `{server_type}`")
        return None



async def ping_all_and_save(at_once: int=200, verbose: bool=True):
    print("Starting...")

    with Session(ENGINE) as session:
        for servers in session.scalars(select(Server)).partitions(at_once):
            records = [record for record in await asyncio.gather(*[ping_server(server.ip_port, server.type) for server in servers]) if record is not None]

            for record in records:
                if verbose:
                    pp(record, compact=True)

                session.merge(Record(**record))


            print("Committing...")
            session.commit()
            print("Ok!")



if __name__ == '__main__':
    with asyncio.Runner() as runner:
        runner.run(ping_all_and_save())
