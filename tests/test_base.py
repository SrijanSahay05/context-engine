from sqlalchemy import Column, Index, Integer, MetaData, Table, UniqueConstraint

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
