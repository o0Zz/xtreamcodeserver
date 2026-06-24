from xtreamcodeserver.entry.serie import XTreamCodeSerie

class TestEntryGrouping:
    """Auto-generated entry ids must be case- and spacing-insensitive so that the
    same serie split across differently-formatted filenames is grouped together
    (e.g. "Malcolm in the Middle" and "Malcolm.In.The.Middle")."""

    def test_serie_id_is_case_insensitive(self):
        a = XTreamCodeSerie(name="Malcolm in the Middle")
        b = XTreamCodeSerie(name="Malcolm In The Middle")
        assert a.get_entry_id() == b.get_entry_id()

    def test_serie_id_is_spacing_insensitive(self):
        a = XTreamCodeSerie(name="Malcolm in the Middle")
        b = XTreamCodeSerie(name="Malcolm  in the   Middle")
        assert a.get_entry_id() == b.get_entry_id()

    def test_display_name_is_preserved(self):
        # Only the id is normalized, the displayed name keeps its original casing.
        serie = XTreamCodeSerie(name="Malcolm In The Middle")
        assert serie.get_name() == "Malcolm In The Middle"

    def test_different_series_keep_different_ids(self):
        a = XTreamCodeSerie(name="Malcolm in the Middle")
        b = XTreamCodeSerie(name="Breaking Bad")
        assert a.get_entry_id() != b.get_entry_id()