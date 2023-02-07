import unittest

from html_msg_generator.generate_html_msg import generate_html_msg

class TestStringMethods(unittest.TestCase):

    def parameter_test(self, value, msg_obj):
        lines = msg_obj.split('\n')
        line_no = 0
        test_value = str()
        for line in lines:
            line_no += 1
            if value in line:
                test_value = line
                break
        self.assertEqual(line_no, self.EXPECTED_LINE)
        self.assertTrue(test_value.find(self.EXPECTED_VALUE) != -1)

    def test_firma_adi(self):
        FIRMA_ADI = "Makrosum"
        self.EXPECTED_LINE = 157
        self.EXPECTED_VALUE = "<strong>Makrosum</strong>"
        msg = generate_html_msg(FIRMA_ADI, "", "", "", "", "", "")
        self.parameter_test(FIRMA_ADI, msg)

    def test_alici_unvani(self):
        ALICI_UNVANI = "Serkan AYAS"
        self.EXPECTED_LINE = 228
        self.EXPECTED_VALUE = "<p>Sayın <b>    Serkan AYAS ,</b> <br>"
        msg = generate_html_msg("", ALICI_UNVANI, "", "", "", "", "")
        lines = msg.split('\n')
        self.parameter_test(ALICI_UNVANI, msg)


    def test_satici_unvani(self):
        SATICI_UNVANI = "Rıdvan Abi"
        self.EXPECTED_LINE = 230
        self.EXPECTED_VALUE = "<b> Rıdvan Abi</b> firmasından"
        msg = generate_html_msg("", "", SATICI_UNVANI, "", "", "", "")
        self.parameter_test(SATICI_UNVANI, msg)

    def test_tarih(self):
        TARIH = "2023-02-07"
        self.EXPECTED_LINE = 231
        self.EXPECTED_VALUE = "<b>2023-02-07</b> tarihli"
        msg = generate_html_msg("", "", "", TARIH, "", "", "")
        self.parameter_test(TARIH, msg)

    def test_fatura_numarasi(self):
        FATURA_NUMARASI = "1357924680"
        self.EXPECTED_LINE = 232
        self.EXPECTED_VALUE = "<b>1357924680</b> numaral"
        msg = generate_html_msg("", "", "", "", FATURA_NUMARASI, "", "")
        self.parameter_test(FATURA_NUMARASI, msg)

    def test_fiyat(self):
        FIYAT = "1357924680"
        self.EXPECTED_LINE = 233
        self.EXPECTED_VALUE = "<b>1357924680</b> tutarında"
        msg = generate_html_msg("", "", "", "", "", FIYAT, "")
        self.parameter_test(FIYAT, msg)

    def test_ticari_temel(self):
        TICARY_TEMEL = "xyz ticari temel"
        self.EXPECTED_LINE = 234
        self.EXPECTED_VALUE = "<b>  xyz ticari temel </b> gelmiştir."
        msg = generate_html_msg("", "", "", "", "", "", TICARY_TEMEL)
        self.parameter_test(TICARY_TEMEL, msg)

