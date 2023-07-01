import typing as t

from flask import Flask, render_template, url_for, abort, request

from sqlalchemy import or_, Column, ColumnElement, ColumnExpressionArgument, BinaryExpression
from sqlalchemy.orm import Session

from mcst.database.engine import ENGINE
from mcst.database.models import DBBase, Server, Record, Player


WEB = Flask(__name__)


def create_filter(model: t.Type[DBBase], request_args: dict[str, str], blacklist: list[str]=[]) -> ColumnElement[bool]:
    filter_list: list[BinaryExpression] = []

    for key, value in request_args.items():
        if key not in blacklist and hasattr(model, key):
            column: Column = getattr(model, key)
            filter_list.append(column.like(f"%{value}%"))

    return or_(*filter_list)



def _generic_list(model: t.Type[DBBase], template_file: str, order_by: ColumnExpressionArgument[t.Any], page: int=1, per_page: int=500) -> str:
    if page < 1:
        abort(400, "Page number cannot be less than 1.")


    filter = create_filter(model, request.args)

    with Session(ENGINE) as session:
        results = session.execute(session.query(model).filter(filter).order_by(order_by).limit(per_page).offset(per_page * (page - 1))).scalars()

        return render_template(template_file, data=results, current_page=page)



@WEB.get("/")
@WEB.get("/<int:page>")
def server_list(page: int=1):
    return _generic_list(Server, "server_list.html", order_by=Server.discovered_at.desc(), page=page)


@WEB.get("/records")
@WEB.get("/records/<int:page>")
def records_list(page: int=1):
    return _generic_list(Record, "records_list.html", order_by=Record.timestamp.desc(), page=page)
