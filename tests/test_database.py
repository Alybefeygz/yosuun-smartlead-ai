"""Integration tests for the SQLite persistence boundary."""

import sqlite3

from app.database import get_db, init_db, lead_ekle, tum_leadler


def test_init_db_is_idempotent(app):
    init_db(app)
    init_db(app)

    with app.app_context():
        assert tum_leadler() == []


def test_get_db_reuses_connection_inside_same_context(app):
    with app.app_context():
        first_connection = get_db()
        second_connection = get_db()

        assert first_connection is second_connection
        assert first_connection.row_factory is sqlite3.Row


def test_lead_ekle_returns_id_and_persists_all_fields(app):
    with app.app_context():
        lead_id = lead_ekle(
            "Ayşe Yılmaz",
            "05550000000",
            "Ajans paketleri hakkında bilgi istiyorum.",
        )
        leads = tum_leadler()

    assert lead_id > 0
    assert leads == [
        {
            "id": lead_id,
            "isim": "Ayşe Yılmaz",
            "telefon": "05550000000",
            "mesaj": "Ajans paketleri hakkında bilgi istiyorum.",
            "tarih": leads[0]["tarih"],
        }
    ]
    assert leads[0]["tarih"]


def test_optional_message_can_be_null(app):
    with app.app_context():
        lead_ekle("Deniz", "05551111111")

        assert tum_leadler()[0]["mesaj"] is None


def test_tum_leadler_returns_newest_first_as_plain_dicts(app):
    with app.app_context():
        first_id = lead_ekle("Birinci", "05550000001", "ilk")
        second_id = lead_ekle("İkinci", "05550000002", "ikinci")
        third_id = lead_ekle("Üçüncü", "05550000003", "üçüncü")
        leads = tum_leadler()

    assert [lead["id"] for lead in leads] == [third_id, second_id, first_id]
    assert all(type(lead) is dict for lead in leads)


def test_parameter_binding_preserves_sql_like_input(app):
    sql_like_name = "Robert'); DROP TABLE leads;--"

    with app.app_context():
        lead_ekle(sql_like_name, "05550000003", "normal mesaj")
        lead_ekle("Tablo Hâlâ Var", "05550000004", "ikinci kayıt")
        leads = tum_leadler()

    assert len(leads) == 2
    assert {lead["isim"] for lead in leads} == {
        sql_like_name,
        "Tablo Hâlâ Var",
    }
