import typing as t

from flask import Flask, render_template, abort, request

from sqlalchemy import or_, Column, ColumnElement, ColumnExpressionArgument, BinaryExpression
from sqlalchemy.orm import Session

from mcst.database.engine import ENGINE
from mcst.database.models import DBBase, Server, Record, Player


WEB = Flask(__name__)
WEB.jinja_env.add_extension('jinja2.ext.do')


def create_filter(model: t.Type[DBBase], request_args: dict[str, str], blacklist: list[str]=[]) -> ColumnElement[bool]:
    filter_list: list[BinaryExpression] = []

    for key, value in request_args.items():
        if key not in blacklist and hasattr(model, key):
            column: Column = getattr(model, key)
            filter_list.append(column.like(f"%{value}%"))

    return or_(*filter_list)



def _generic_list(model: t.Type[DBBase], template_file: str, filter: ColumnElement[bool], order_by: ColumnExpressionArgument[t.Any], page: int=1, per_page: int=100) -> str:
    if page < 1:
        abort(400, "Page number cannot be less than 1.")

    with Session(ENGINE) as session:
        results = session.execute(session.query(model).filter(filter).order_by(order_by).limit(per_page).offset(per_page * (page - 1))).scalars()

        return render_template(template_file, result=results, current_page=page)



def _generic_one(model: t.Type[DBBase], template_file: str, *filter) -> str:
    with Session(ENGINE) as session:
        server = session.query(model).filter(*filter).one_or_none()

        if server is None:
            abort(404, f"{type(model).__name__} with `{filter}` is not tracked (yet).")


        return render_template(template_file, result=server)



@WEB.get("/")
@WEB.get("/<int:page>")
def server_list(page: int=1):
    return _generic_list(
        Server, "server_list.html", create_filter(Server, request.args),
        order_by=Server.discovered_at.desc(), page=page
    )


@WEB.get("/<string:server_host>")
def server(server_host: str):
    return _generic_one(Server, "server.html", Server.ip_port == server_host)



@WEB.get("/records")
@WEB.get("/records/<int:page>")
def records_list(page: int=1):
    return _generic_list(
        Record, "records_list.html", create_filter(Server, request.args, blacklist=["players"]),
        order_by=Record.timestamp.desc(), page=page
    )



@WEB.get("/players")
@WEB.get("/players/<int:page>")
def players_list(page: int=1):
    return _generic_list(
        Player, "players_list.html", create_filter(Player, request.args),
        order_by=Player.username, page=page
    )


@WEB.get("/player/<string:player_uuid>")
def player(player_uuid: str):
    return _generic_one(Player, "player.html", Player.uuid == player_uuid)
