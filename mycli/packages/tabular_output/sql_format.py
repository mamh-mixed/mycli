"""Format adapter for sql."""

from typing import Generator, Union

from cli_helpers.tabular_output import TabularOutputFormatter

from mycli.packages.parseutils import extract_tables_from_complete_statements

supported_formats = (
    "sql-insert",
    "sql-update",
    "sql-update-1",
    "sql-update-2",
)

preprocessors = ()

formatter: TabularOutputFormatter


def escape_for_sql_statement(value: Union[bytes, str]) -> str:
    if isinstance(value, bytes):
        return f"X'{value.hex()}'"
    else:
        return formatter.mycli.sqlexecute.conn.escape(value)


def adapter(data: list[str], headers: list[str], table_format: Union[str, None] = None, **kwargs) -> Generator[str, None, None]:
    tables = extract_tables_from_complete_statements(formatter.query)
    if len(tables) > 0:
        table = tables[0]
        if table[0]:
            table_name = "{}.{}".format(*table[:2])
        else:
            table_name = table[1]
    else:
        table_name = "`DUAL`"
    if table_format == "sql-insert":
        h = "`, `".join(headers)
        yield "INSERT INTO {} (`{}`) VALUES".format(table_name, h)
        prefix = "  "
        for d in data:
            values = ", ".join(escape_for_sql_statement(v) for i, v in enumerate(d))
            yield "{}({})".format(prefix, values)
            if prefix == "  ":
                prefix = ", "
        yield ";"
    if table_format and table_format.startswith("sql-update"):
        s = table_format.split("-")
        keys = 1
        if len(s) > 2:
            keys = int(s[-1])
        for d in data:
            yield "UPDATE {} SET".format(table_name)
            prefix = "  "
            for i, v in enumerate(d[keys:], keys):
                yield "{}`{}` = {}".format(prefix, headers[i], escape_for_sql_statement(v))
                if prefix == "  ":
                    prefix = ", "
            f = "`{}` = {}"
            where = (f.format(headers[i], escape_for_sql_statement(d[i])) for i in range(keys))
            yield "WHERE {};".format(" AND ".join(where))


def register_new_formatter(tof: TabularOutputFormatter):
    global formatter
    formatter = tof
    for sql_format in supported_formats:
        tof.register_new_formatter(sql_format, adapter, preprocessors, {"table_format": sql_format})
