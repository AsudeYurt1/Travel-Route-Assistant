import json
import webbrowser
from math import radians, sin, cos, sqrt, atan2
from transformers import pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
import tkinter as tk
from tkinter import messagebox, scrolledtext
import folium

# Haversine formülü
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Model ayarları
model_id = "google/flan-t5-base"
pipe = pipeline("text2text-generation", model=model_id, max_new_tokens=250)
llm = HuggingFacePipeline(pipeline=pipe)

# JSON yolu ve şehir merkezi
json_path = r"C:\Users\w10\Desktop\istanbul\Istanbul_gezilecekyerler.json"
city_center = (41.0082, 28.9784)

try:
    with open(json_path, "r", encoding="utf-8") as f:
        places = json.load(f)
except FileNotFoundError:
    print("JSON dosyası bulunamadı.")
    exit()

# Haritayı oluştur
def show_on_map(top_5):
    map_center = city_center
    m = folium.Map(location=map_center, zoom_start=13)

    # Merkez
    folium.Marker(
        location=map_center,
        popup="Şehir Merkezi",
        icon=folium.Icon(color='red')
    ).add_to(m)

    # Yerleri işaretle
    for i, place in enumerate(top_5, 1):
        folium.Marker(
            location=(place["lat"], place["lon"]),
            popup=f"{i}. {place['name']}",
            tooltip=place["name"],
            icon=folium.Icon(color='blue', icon="info-sign")
        ).add_to(m)

    map_path = "gezilecek_yerler_harita.html"
    m.save(map_path)
    webbrowser.open(map_path)

# tkinter callback
def generate_itinerary():
    category = category_entry.get().strip().lower()
    filtered = [p for p in places if p["category"].lower() == category]
    
    if not filtered:
        messagebox.showerror("Kategori Bulunamadı", f"{category} kategorisinde yer bulunamadı.")
        return

    for p in filtered:
        p["distance_from_center"] = haversine(city_center[0], city_center[1], p["lat"], p["lon"])

    sorted_places = sorted(filtered, key=lambda x: x["distance_from_center"])
    top_5 = sorted_places[:5]

    places_text = ", ".join([p["name"] for p in top_5])
    prompt = (
        f"Create a detailed sightseeing itinerary for Istanbul, specifically for the {category} category places. "
        "For each place, provide the name, the order to visit it, and most importantly, a short explanation of why each place is significant and worth visiting. "
        f"Here are the places to visit: {places_text}."
    )

    results_text.delete("1.0", tk.END)
    results_text.insert(tk.END, f"{category} kategorisindeki en yakın 5 yer:\n\n")
    for i, place in enumerate(top_5, 1):
        results_text.insert(tk.END, f"{i}. {place['name']} ({place['distance_from_center']:.2f} km)\n")
    
    results_text.insert(tk.END, "\nYapay Zeka Önerilen Rota:\n\n")
    try:
        response = llm(prompt)
        results_text.insert(tk.END, response)
    except Exception as e:
        results_text.insert(tk.END, f"Model hatası: {str(e)}")

    show_on_map(top_5)

# tkinter GUI
window = tk.Tk()
window.title("İstanbul Gezi Rota Asistanı")
window.geometry("700x600")

tk.Label(window, text="Kategori Giriniz (ör: museum, historical, park):").pack(pady=5)
category_entry = tk.Entry(window, width=50)
category_entry.pack(pady=5)

tk.Button(window, text="Önerileri Al ve Haritada Göster", command=generate_itinerary).pack(pady=10)

results_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=30)
results_text.pack(padx=10, pady=10)

window.mainloop()
