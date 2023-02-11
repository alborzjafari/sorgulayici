from jinja2 import Environment, FileSystemLoader
import os

def generate_html_msg(firma_adi, alici_unvani, satici_unvani, tarih,
                      fatura_numarasi, fiyat, ticari_temel):
    root = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(root, './')
    env = Environment(loader = FileSystemLoader(templates_dir))
    template = env.get_template('e_arsiv_imza_template.html')
    filename = os.path.join(root, 'html', 'e_arsiv_imza.html')
    return template.render(
            firma_adi = firma_adi,
            alici_unvani = alici_unvani,
            satici_unvani = satici_unvani,
            tarih = tarih,
            fatura_numarasi = fatura_numarasi,
            fiyat = fiyat,
            ticari_temel = ticari_temel)

if __name__ == "__main__":
    print(generate_html_msg("Makrosum", "Serkan AYAS", "Rıdvan Abi", "2023-01-03", "12345", "100", "xyc tic temel"))
