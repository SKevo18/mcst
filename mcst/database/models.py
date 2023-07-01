import typing as t

from datetime import datetime

from sqlalchemy import String, Text, Integer, JSON, ForeignKey, Column, Table, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship



class DBBase(DeclarativeBase):
    type_annotation_map = {
        dict: JSON
    }


class Server(DBBase):
    """
        There can only be one server. A server can have multiple records (historical ping data).
    """

    __tablename__ = 'servers'
    ip_port: Mapped[str] = mapped_column(String(64), primary_key=True)
    """IP and port of the server, separated by `:`"""
    discovered_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    """When was this server first scraped?"""

    name: Mapped[str] = mapped_column(String(255), nullable=True)
    """Server name, as shown in the source"""
    type: Mapped[str] = mapped_column(String(7), default='java', nullable=False)
    """Server type, either `java` or `bedrock`."""
    source: Mapped[str] = mapped_column(String(150), default='unknown', nullable=False)
    """The source (URL) of the server"""

    records: Mapped[list['Record']] = relationship("Record", back_populates='server', cascade="all, delete")
    """A list of ping records for this server"""


    def __repr__(self) -> str:
        return f"<Server {self.ip_port}>"



player_record_association = Table(
    "player_record",
    DBBase.metadata,
    Column("player_uuid", String(36), ForeignKey("players.uuid"), primary_key=True),
    Column("record_id", Integer, ForeignKey("records.id"), primary_key=True)
)



class Record(DBBase):
    """
        A server record represents a scrapped server result.
    """

    __tablename__ = 'records'
    id: Mapped[int] = mapped_column(primary_key=True)
    """Sometimes `timestamp` isn't unique, so this is purely just for relationships"""

    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())
    """The date and time when this record was created"""
    server_id: Mapped[str] = mapped_column(ForeignKey(Server.ip_port, ondelete='CASCADE'))
    """The ID of the server this record belongs to"""

    query: Mapped[bool] = mapped_column(default=False, nullable=False)
    """Whether query was used to fetch the server status"""

    max_players: Mapped[int]
    """Maximum number of players online"""
    online_players: Mapped[int]
    """Current amount of players online"""

    motd: Mapped[t.Text] = mapped_column(Text, default="A Minecraft Server")
    """Server MOTD (as shown in the server list)"""
    latency: Mapped[float]
    """Server ping"""

    version: Mapped[str] = mapped_column(String(255))
    """Version number (as shown in the server list)"""
    version_brand: Mapped[t.Optional[str]] = mapped_column(String(255))
    """Bedrock: `MCPE` or `MCEE`, Java: any brand sent by query response"""

    map_name: Mapped[t.Optional[str]] = mapped_column(String(100))
    """World name (Java: via query only)"""
    gamemode: Mapped[t.Optional[str]] = mapped_column(String(10))
    """The name of the gamemode on the server (Bedrock only)"""
    icon: Mapped[t.Optional[t.Text]] = mapped_column(Text)
    """Server icon (base64 encoded PNG, Java only)"""
    plugins: Mapped[dict]
    """List of plugins, if present (Java only)"""


    server: Mapped[Server] = relationship("Server", back_populates='records')
    """A server this record belongs to"""
    players = relationship('Player', secondary=player_record_association, back_populates="records")
    """A list of players this record has"""


    def __repr__(self) -> str:
        return f"<Record>"



class Player(DBBase):
    """
        A Minecraft player. There can be multiple players of the same username (for offline accounts).
    """

    __tablename__ = 'players'
    uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    """
        The UUID of player. Should be unique for both premium and cracked accounts.

        Offline account UUIDs are generated with UUIDv3 and Mojang UUIDs (online) with UUIDv4

        Ref.: https://www.spigotmc.org/threads/441348/
    """
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    """The username of the player"""

    premium: Mapped[bool] = mapped_column(default=True, nullable=False)
    """
        Whether the account is premium or offline

        Legend:

        - `premium`: standard Minecraft account
        - `offline`: offline (AKA. "cracked") account
    """

    first_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
    """When was this account first seen at?"""


    records = relationship('Record', secondary=player_record_association, back_populates="players")
    """A list of record relationships for this player"""


    def __repr__(self) -> str:
        return f"<Player {self.uuid}:{self.username}>"



def create_tables(engine: Engine) -> None:
    DBBase.metadata.create_all(engine)



if __name__ == '__main__':
    from mcst.database.engine import ENGINE

    create_tables(ENGINE)
