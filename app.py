import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import openai
import requests
import io
import os
from datetime import datetime

# OpenAI API einrichten
openai.api_key = os.getenv("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")

# Farben aus Guidelines
COLORS = {
    "red": "#F03C32",
    "orange": "#FAA023",
    "yellow": "#FFD200",
    "green": "#19AA5A",
    "blue": "#0091F0",
    "purple": "#5A3296",
    "petrol": "#007A7A",  # Annahme für Petrol
    "white": "#FFFFFF",
    "black": "#000000"
}

# Fonts laden (Karla von Google Fonts herunterladen, falls nicht lokal)
def load_font(size, bold=False):
    font_url = "https://fonts.gstatic.com/s/karla/v23/qkBIXvYC6trAT55ZBi1ueQVIjQTDeJqqFENLR7fHGw.ttf" if bold else "https://fonts.gstatic.com/s/karla/v23/qkB9XvYC6trAT55ZBi1ueQVIjQTD-JqqFENLR7fHGw.ttf"
    font_data = requests.get(font_url).content
    return ImageFont.truetype(io.BytesIO(font_data), size)

# Logo laden (ersetze mit deinen Pfaden)
LOGO_PETROL = Image.open("assets/tsp_logo_petrol.png")  # Petrol-Variante
LOGO_WHITE = Image.open("assets/tsp_logo_white.png")    # Weiße Variante

# Funktion für Text-Overlay auf Bild (konform zu Guidelines)
def overlay_text_on_image(image, headline, subheadline, highlight_word, highlight_color, logo_variant="white", text_position="bottom", logo_position="top_left"):
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # Abdunkelung für Text (linearer Verlauf unten)
    gradient = Image.new('RGBA', (width, height // 3), (0, 0, 0, 0))
    for y in range(height // 3):
        alpha = int(255 * (y / (height // 3)))
        draw_grad = ImageDraw.Draw(gradient)
        draw_grad.rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
    image.paste(gradient, (0, height - height // 3), gradient)
    
    # Fonts
    headline_font = load_font(80, bold=True)  # 70-85 px
    subheadline_font = load_font(50)         # 40-55 px
    
    # Headline mit Highlight
    headline_parts = headline.split(highlight_word)
    headline_text = headline_parts[0] + highlight_word + headline_parts[1]
    # Zeichne Text (Beispiel: unten links)
    y_pos = height - height // 3 + 50 if text_position == "bottom" else 50
    draw.text((65, y_pos), headline_parts[0], font=headline_font, fill=COLORS["white"])
    text_width = draw.textsize(headline_parts[0], font=headline_font)[0]
    draw.text((65 + text_width, y_pos), highlight_word, font=headline_font, fill=highlight_color)
    text_width += draw.textsize(highlight_word, font=headline_font)[0]
    draw.text((65 + text_width, y_pos), headline_parts[1], font=headline_font, fill=COLORS["white"])
    
    # Subheadline
    draw.text((65, y_pos + 100), subheadline, font=subheadline_font, fill=COLORS["white"])
    
    # Logo mit Schlagschatten
    logo = LOGO_WHITE if logo_variant == "white" else LOGO_PETROL
    logo = logo.resize((200, 200))  # Anpassen
    shadow = logo.filter(ImageFilter.GaussianBlur(50))
    shadow_enh = ImageEnhance.Color(shadow).enhance(0)  # Schwarz
    shadow_enh = ImageEnhance.Brightness(shadow_enh).enhance(0.5)
    x_logo = 65 if "left" in logo_position else (width - 265) if "right" in logo_position else (width // 2 - 100)
    y_logo = 65 if "top" in logo_position else height - 265
    image.paste(shadow_enh, (x_logo, y_logo), shadow_enh)
    image.paste(logo, (x_logo, y_logo), logo)
    
    return image

# Funktion für Hashtags generieren
def generate_hashtags(theme):
    base_tags = ["#Tierschutz", "#Umweltschutz", "#MitgefühlWählen", "#TSP", "#ParteiMenschUmweltTierschutz", "#WeilJedesLebenWertvollIst"]
    # AI-generiert ergänzen
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Generiere 5 relevante Hashtags für TSP-Thema: {theme}"}]
    )
    return base_tags + response.choices[0].message.content.split()

# Modus 1: Bild analysieren
def analyze_image(image):
    # Speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image.save(f"uploads/{timestamp}.png")
    
    # Analyse mit GPT-4 Vision
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_to_base64(image)}"}}, {"type": "text", "text": "Analysiere das Bild und generiere einen positiven Social-Media-Text (Headline + Subheadline) im TSP-Stil: positiv, emotional, konform zu Guidelines."}]}
    )
    text = response.choices[0].message.content
    headline, subheadline = text.split("\n")[:2]  # Annahme
    highlight_word = "leben"  # Beispiel, AI könnte vorschlagen
    hashtags = generate_hashtags("Bildanalyse")
    return headline, subheadline, highlight_word, hashtags

# Hilfsfunktion: Bild zu Base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Modus 2: Bild aus Text generieren
def generate_image_from_text(text):
    # DALL-E Prompt, konform zu Guidelines
    prompt = f"Generiere ein positives, emotionales Bild im TSP-Stil: {text}. Optimismus, Harmonie, warme Töne, Blickkontakt, keine Kinder erkennbar, ruhig."
    response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    image_url = response['data'][0]['url']
    image_data = requests.get(image_url).content
    image = Image.open(io.BytesIO(image_data)).resize((1080, 1350))
    return image

# Streamlit App
st.title("TSP Social Media Generator")
st.write("Erstelle konforme Inhalte basierend auf Guidelines V.052025")

mode = st.radio("Wähle Modus:", ("Bild hochladen (Analyse)", "Text eingeben (Bild generieren)"))

if mode == "Bild hochladen (Analyse)":
    uploaded_file = st.file_uploader("Lade ein Bild hoch", type=["png", "jpg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Hochgeladenes Bild")
        if st.button("Analysieren"):
            headline, subheadline, highlight_word, hashtags = analyze_image(image)
            text_output = f"Headline: {headline}\nSubheadline: {subheadline}\nHashtags: {' '.join(hashtags)}"
            st.text_area("Generierter Text + Hashtags", text_output)
            st.download_button("Download als TXT", text_output, file_name="social_text.txt")

elif mode == "Text eingeben (Bild generieren)":
    text_input = st.text_area("Gib einen Text ein (z.B. Thema für Post)")
    if text_input and st.button("Generieren"):
        image = generate_image_from_text(text_input)
        # Overlay Text (Beispielwerte, passe an)
        highlight_color = COLORS["orange"]
        image = overlay_text_on_image(image, "In welcher Welt", "möchtest du leben?", "leben", highlight_color)
        st.image(image, caption="Generiertes Bild mit Overlay")
        hashtags = generate_hashtags(text_input)
        st.text("Hashtags: " + " ".join(hashtags))
        
        # Downloads für Kanäle
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        st.download_button("Download Instagram (1080x1350)", buffered.getvalue(), file_name="instagram.png")
        # Resize für andere Kanäle
        twitter_img = image.resize((1200, 675))
        buffered_tw = io.BytesIO()
        twitter_img.save(buffered_tw, format="PNG")
        st.download_button("Download Twitter/X (1200x675)", buffered_tw.getvalue(), file_name="twitter.png")
        fb_img = image.resize((1200, 630))
        buffered_fb = io.BytesIO()
        fb_img.save(buffered_fb, format="PNG")
        st.download_button("Download Facebook (1200x630)", buffered_fb.getvalue(), file_name="facebook.png")

# Ordner für Uploads erstellen
if not os.path.exists("uploads"):
    os.makedirs("uploads")
