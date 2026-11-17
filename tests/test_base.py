import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Table,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.schema import CreateIndex

from db.base import Base


def test_composite_indexes_and_unique_constraints_have_distinct_names() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    first_unique = UniqueConstraint("a", "b")
    second_unique = UniqueConstraint("a", "c")
    table = Table(
        "sample",
        metadata,
        Column("a", Integer),
        Column("b", Integer),
        Column("c", Integer),
        first_unique,
        second_unique,
    )
    first_index = Index(None, table.c.a, table.c.b)
    second_index = Index(None, table.c.a, table.c.c)

    assert first_index.name == "sample_a_b_idx"
    assert second_index.name == "sample_a_c_idx"
    assert first_unique.name == "sample_a_b_key"
    assert second_unique.name == "sample_a_c_key"


def test_foreign_key_names_include_all_columns_and_targets() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    for name in ("parents", "alternates"):
        Table(
            name,
            metadata,
            Column("scope_id", Integer),
            Column("id", Integer),
            Column("legacy_id", Integer),
        )
    composite = ForeignKeyConstraint(
        ["scope_id", "parent_id"], ["parents.scope_id", "parents.id"]
    )
    other_table = ForeignKeyConstraint(["parent_id"], ["alternates.id"])
    other_column = ForeignKeyConstraint(["parent_id"], ["parents.legacy_id"])
    simple = ForeignKeyConstraint(["parent_id"], ["parents.id"])
    Table(
        "children",
        metadata,
        Column("scope_id", Integer),
        Column("parent_id", Integer),
        composite,
        other_table,
        other_column,
        simple,
    )
    assert composite.name == "children_scope_id_parent_id_parents_scope_id_id_fkey"
    assert len({c.name for c in (composite, other_table, other_column, simple)}) == 4


def test_check_constraints_require_descriptive_names() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    check = CheckConstraint("amount >= 0", name="amount_nonnegative")
    table = Table("payments", metadata, Column("amount", Integer), check)
    assert check.name == "payments_amount_nonnegative_check"
    assert table.primary_key.name == "payments_pkey"
    with pytest.raises(InvalidRequestError, match="explicitly named"):
        table.append_constraint(CheckConstraint("amount < 100"))


def test_postgresql_truncates_long_generated_names_deterministically() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    table = Table(
        "memory_source_associations",
        metadata,
        Column("original_conversation_identifier", Integer),
        Column("original_message_identifier", Integer),
        Column("alternate_message_identifier", Integer),
    )
    first = Index(
        None,
        table.c.original_conversation_identifier,
        table.c.original_message_identifier,
    )
    second = Index(
        None,
        table.c.original_conversation_identifier,
        table.c.alternate_message_identifier,
    )
    dialect = create_engine("postgresql+psycopg://").dialect
    first_ddl = str(CreateIndex(first).compile(dialect=dialect))
    second_ddl = str(CreateIndex(second).compile(dialect=dialect))
    first_name = first_ddl.split()[2]
    second_name = second_ddl.split()[2]
    assert len(first_name.encode("utf-8")) <= dialect.max_identifier_length
    assert len(second_name.encode("utf-8")) <= dialect.max_identifier_length
    assert first_name != second_name
    assert first_ddl == str(CreateIndex(first).compile(dialect=dialect))


def test_specialized_indexes_preserve_explicit_names() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    table = Table("sample", metadata, Column("value", Integer))
    expression = Index("sample_abs_value_idx", func.abs(table.c.value))
    partial = Index(
        "sample_positive_value_idx", table.c.value, postgresql_where=table.c.value > 0
    )
    assert expression.name == "sample_abs_value_idx"
    assert partial.name == "sample_positive_value_idx"
