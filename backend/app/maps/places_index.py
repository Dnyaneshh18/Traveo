"""
Offline place index (Pune) used by the local maps provider for autosuggest &
reverse geocoding.  With Mappls configured these are only a fallback.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.core.geo import LatLng, haversine_km
from app.maps.provider import PlaceSuggestion

# name, address, lat, lng, category
PUNE_PLACES: list[tuple[str, str, float, float, str]] = [
    ("Hinjewadi Phase 1", "Rajiv Gandhi Infotech Park, Hinjewadi, Pune", 18.5912, 73.7389, "area"),
    ("Hinjewadi Phase 2", "Hinjewadi Phase 2, Pune", 18.5990, 73.7100, "area"),
    ("Hinjewadi Phase 3", "Hinjewadi Phase 3, Pune", 18.5870, 73.6850, "area"),
    ("Wakad", "Wakad, Pimpri-Chinchwad, Pune", 18.5975, 73.7620, "area"),
    ("Baner", "Baner, Pune", 18.5590, 73.7868, "area"),
    ("Balewadi High Street", "Balewadi, Pune", 18.5680, 73.7746, "landmark"),
    ("Aundh", "Aundh, Pune", 18.5590, 73.8075, "area"),
    ("Pashan", "Pashan, Pune", 18.5364, 73.7929, "area"),
    ("Bavdhan", "Bavdhan, Pune", 18.5150, 73.7780, "area"),
    ("Kothrud", "Kothrud, Pune", 18.5074, 73.8077, "area"),
    ("Kothrud Depot", "Kothrud Bus Depot, Pune", 18.5040, 73.8130, "transit"),
    ("Karve Nagar", "Karve Nagar, Pune", 18.4900, 73.8220, "area"),
    ("Warje", "Warje, Pune", 18.4820, 73.8020, "area"),
    ("Sinhagad Road", "Sinhagad Road, Pune", 18.4750, 73.8250, "area"),
    ("Dhayari", "Dhayari, Pune", 18.4520, 73.8100, "area"),
    ("Katraj", "Katraj, Pune", 18.4480, 73.8580, "area"),
    ("Katraj Chowk", "Katraj Chowk, Pune-Satara Road", 18.4520, 73.8600, "landmark"),
    ("Bibwewadi", "Bibwewadi, Pune", 18.4750, 73.8650, "area"),
    ("Swargate", "Swargate Bus Stand, Pune", 18.5018, 73.8636, "transit"),
    ("Shivajinagar", "Shivajinagar, Pune", 18.5314, 73.8446, "area"),
    ("Shivajinagar Bus Stand", "Shivajinagar ST Stand, Pune", 18.5308, 73.8480, "transit"),
    ("Pune Railway Station", "Pune Junction, Agarkar Nagar", 18.5286, 73.8743, "transit"),
    ("Deccan Gymkhana", "Deccan Gymkhana, Pune", 18.5158, 73.8410, "area"),
    ("FC Road", "Fergusson College Road, Pune", 18.5220, 73.8410, "landmark"),
    ("JM Road", "Jangali Maharaj Road, Pune", 18.5250, 73.8460, "landmark"),
    ("Camp", "Camp / MG Road, Pune", 18.5150, 73.8790, "area"),
    ("Koregaon Park", "Koregaon Park, Pune", 18.5362, 73.8939, "area"),
    ("Kalyani Nagar", "Kalyani Nagar, Pune", 18.5480, 73.9030, "area"),
    ("Viman Nagar", "Viman Nagar, Pune", 18.5679, 73.9143, "area"),
    ("Phoenix Marketcity", "Viman Nagar, Pune", 18.5620, 73.9167, "landmark"),
    ("Pune Airport", "Lohegaon Airport, Pune", 18.5822, 73.9197, "transit"),
    ("Kharadi", "Kharadi, Pune", 18.5515, 73.9410, "area"),
    ("EON IT Park", "EON Free Zone, Kharadi, Pune", 18.5518, 73.9500, "landmark"),
    ("Magarpatta City", "Magarpatta, Hadapsar, Pune", 18.5150, 73.9280, "area"),
    ("Hadapsar", "Hadapsar, Pune", 18.5089, 73.9260, "area"),
    ("Amanora Park Town", "Amanora, Hadapsar, Pune", 18.5190, 73.9390, "landmark"),
    ("Wanowrie", "Wanowrie, Pune", 18.4890, 73.9000, "area"),
    ("Kondhwa", "Kondhwa, Pune", 18.4680, 73.8930, "area"),
    ("NIBM Road", "NIBM Road, Kondhwa, Pune", 18.4750, 73.9040, "area"),
    ("Undri", "Undri, Pune", 18.4590, 73.9190, "area"),
    ("Yerwada", "Yerwada, Pune", 18.5520, 73.8850, "area"),
    ("Pimpri", "Pimpri, Pimpri-Chinchwad", 18.6298, 73.7997, "area"),
    ("Chinchwad", "Chinchwad, Pimpri-Chinchwad", 18.6470, 73.7960, "area"),
    ("Nigdi", "Nigdi, Pimpri-Chinchwad", 18.6500, 73.7700, "area"),
    ("Akurdi", "Akurdi, Pimpri-Chinchwad", 18.6480, 73.7810, "area"),
    ("Ravet", "Ravet, Pimpri-Chinchwad", 18.6480, 73.7430, "area"),
    ("Tathawade", "Tathawade, Pune", 18.6200, 73.7500, "area"),
    ("Punawale", "Punawale, Pune", 18.6260, 73.7350, "area"),
    ("Bhosari", "Bhosari, Pimpri-Chinchwad", 18.6280, 73.8470, "area"),
    ("Dighi", "Dighi, Pune", 18.6150, 73.8730, "area"),
    ("Vishrantwadi", "Vishrantwadi, Pune", 18.5750, 73.8760, "area"),
    ("Dhanori", "Dhanori, Pune", 18.5860, 73.9050, "area"),
    ("Wagholi", "Wagholi, Pune", 18.5800, 73.9800, "area"),
    ("Lonavala", "Lonavala, Maharashtra", 18.7546, 73.4062, "area"),
    ("Talegaon Dabhade", "Talegaon, Pune", 18.7350, 73.6750, "area"),
    ("Chakan", "Chakan, Pune", 18.7600, 73.8630, "area"),
    ("Pune University Circle", "Savitribai Phule Pune University Gate, Ganeshkhind", 18.5530, 73.8250, "landmark"),
    ("Dange Chowk", "Dange Chowk, Thergaon", 18.6180, 73.7700, "landmark"),
    ("Kalewadi Phata", "Kalewadi Phata, Wakad", 18.6100, 73.7760, "landmark"),
    ("Bhumkar Chowk", "Bhumkar Chowk, Wakad", 18.5950, 73.7530, "landmark"),
    ("Chandni Chowk", "Chandni Chowk, Bavdhan", 18.5050, 73.7830, "landmark"),
    ("Paud Road", "Paud Road, Kothrud", 18.5090, 73.8210, "landmark"),
    ("Nal Stop", "Nal Stop, Karve Road", 18.5060, 73.8310, "landmark"),
    ("Dandekar Pul", "Dandekar Bridge, Sinhagad Road", 18.4980, 73.8420, "landmark"),
    ("Sarasbaug", "Sarasbaug, Pune", 18.5000, 73.8520, "landmark"),
    ("Sahakar Nagar", "Sahakar Nagar, Pune", 18.4880, 73.8550, "area"),
    ("Market Yard", "Market Yard, Gultekdi", 18.4900, 73.8680, "landmark"),
    ("Kondhwa Khurd", "Kondhwa Khurd, Pune", 18.4750, 73.8880, "area"),
    ("Manjri", "Manjri, Pune", 18.5000, 73.9800, "area"),
    ("Keshav Nagar", "Keshav Nagar, Mundhwa", 18.5300, 73.9450, "area"),
    ("Mundhwa", "Mundhwa, Pune", 18.5310, 73.9260, "area"),
    ("Sus Road", "Sus Road, Pashan", 18.5450, 73.7850, "area"),
    ("Pimple Saudagar", "Pimple Saudagar, Pune", 18.5990, 73.7970, "area"),
    ("Pimple Nilakh", "Pimple Nilakh, Pune", 18.5820, 73.7890, "area"),
    ("Pimple Gurav", "Pimple Gurav, Pune", 18.5900, 73.8170, "area"),
    ("Sangvi", "Sangvi, Pune", 18.5730, 73.8180, "area"),
    ("Bopodi", "Bopodi, Pune", 18.5680, 73.8340, "area"),
    ("Khadki", "Khadki, Pune", 18.5630, 73.8500, "area"),
    ("Model Colony", "Model Colony, Shivajinagar", 18.5300, 73.8330, "area"),
    ("Erandwane", "Erandwane, Pune", 18.5090, 73.8300, "area"),
    ("Sadashiv Peth", "Sadashiv Peth, Pune", 18.5080, 73.8480, "area"),
    ("Narayan Peth", "Narayan Peth, Pune", 18.5150, 73.8500, "area"),
    ("Shaniwar Wada", "Shaniwar Wada, Pune", 18.5195, 73.8553, "landmark"),
    ("Kasba Peth", "Kasba Peth, Pune", 18.5210, 73.8600, "area"),
    ("Hadapsar Gadital", "Gadital, Hadapsar", 18.5020, 73.9290, "transit"),
    ("Fursungi", "Fursungi, Pune", 18.4800, 73.9700, "area"),
    ("Wadgaon Sheri", "Wadgaon Sheri, Pune", 18.5530, 73.9210, "area"),
    ("Kalas", "Kalas, Vishrantwadi", 18.5850, 73.8790, "area"),
    ("Lohegaon", "Lohegaon, Pune", 18.6000, 73.9300, "area"),
    ("Moshi", "Moshi, Pimpri-Chinchwad", 18.6790, 73.8500, "area"),
    ("Alandi", "Alandi, Pune", 18.6770, 73.8970, "area"),
    ("Dehu Road", "Dehu Road, Pune", 18.6870, 73.7400, "area"),
    ("Kiwale", "Kiwale, Pune", 18.6540, 73.7300, "area"),
    ("Mamurdi", "Mamurdi, Pune", 18.6650, 73.7350, "area"),
    ("Pirangut", "Pirangut, Mulshi", 18.5100, 73.6850, "area"),
    ("Hinjewadi Wipro Circle", "Wipro Circle, Hinjewadi Phase 2", 18.6010, 73.7180, "landmark"),
    ("Infosys Phase 2", "Infosys Campus, Hinjewadi Phase 2", 18.6040, 73.7050, "landmark"),
    ("Blue Ridge Township", "Blue Ridge, Hinjewadi Phase 1", 18.5950, 73.7370, "landmark"),
    ("Symbiosis Viman Nagar", "Symbiosis Campus, Viman Nagar", 18.5680, 73.9150, "college"),
    ("Amba Mata Mandir", "Sukh Sagar Nagar, Katraj-Kondhwa, Pune 411046", 18.4558, 73.8694, "temple"),
    ("Shri Amba Mata Temple", "Appar Road, Sukhsagar Nagar, Katraj, Pune", 18.4560, 73.8690, "temple"),
    ("Ambika Mata Mandir", "Katraj Chowk, Pune", 18.4510, 73.8590, "temple"),
    ("Chaturshringi Temple", "Senapati Bapat Road, Pune", 18.5370, 73.8290, "temple"),
    ("Dagdusheth Halwai Ganpati", "Budhwar Peth, Pune", 18.5165, 73.8560, "temple"),
    ("ISKCON Temple Pune", "Katraj-Kondhwa Bypass Road, Tilekar Nagar, Kondhwa", 18.4540, 73.8820, "temple"),
    ("Parvati Hill Temple", "Parvati Paytha, Pune", 18.4970, 73.8470, "landmark"),
    ("Kasba Ganpati Temple", "Kasba Peth, Pune", 18.5200, 73.8580, "temple"),
    ("Alankapuram Alandi", "Alandi Devasthan, Pune", 18.6750, 73.8980, "temple"),
    ("Mahalaxmi Temple Pune", "Sarasbaug, Pune", 18.5010, 73.8530, "temple"),
    ("BAPS Shri Swaminarayan Mandir", "Narhe Ambegaon Road, Pune", 18.4610, 73.8200, "temple"),
    ("Kanifnath Temple", "Kanifnath Hill, Saswad Road, Pune", 18.4100, 73.9900, "temple"),
    ("Baneshwar Temple", "Nasrapur, Pune", 18.2700, 73.9000, "temple"),
    ("Jejuri Khandoba Mandir", "Jejuri, Pune District", 18.2800, 74.1600, "temple"),
    ("Katraj Snake Park / Zoo", "Rajiv Gandhi Zoological Park, Katraj", 18.4540, 73.8590, "landmark"),
    ("Upper Indira Nagar", "Bibwewadi, Pune", 18.4650, 73.8690, "area"),
    ("Lower Indira Nagar", "Bibwewadi, Pune", 18.4680, 73.8670, "area"),
    ("Chintamani Nagar", "Bibwewadi, Pune", 18.4690, 73.8640, "area"),
    ("Salunke Vihar", "Wanowrie, Pune", 18.4850, 73.8990, "area"),
    ("Lullanagar", "Wanowrie, Pune", 18.4950, 73.8850, "area"),
    ("Fatima Nagar", "Wanowrie, Pune", 18.5030, 73.8990, "area"),
    ("Market Yard Gultekdi", "Market Yard, Pune", 18.4910, 73.8670, "area"),
    ("Marketyard Gangadham", "Gangadham Chowk, Market Yard", 18.4820, 73.8760, "landmark"),
]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def search_places(query: str, near: LatLng | None, limit: int = 8) -> list[PlaceSuggestion]:
    q = _norm(query)
    if len(q) < 2:
        return []
    scored: list[tuple[float, PlaceSuggestion]] = []
    for name, address, lat, lng, category in PUNE_PLACES:
        n = _norm(name)
        a = _norm(address)
        if q in n:
            score = 1.0 + (0.3 if n.startswith(q) else 0.0)
        elif q in a:
            score = 0.7
        else:
            ratio = SequenceMatcher(None, q, n).ratio()
            if ratio < 0.55:
                continue
            score = ratio * 0.8
        dist = haversine_km(near.lat, near.lng, lat, lng) if near else None
        if dist is not None:
            score += max(0.0, 0.25 - dist / 80.0)
        scored.append(
            (
                score,
                PlaceSuggestion(
                    name=name,
                    address=address,
                    lat=lat,
                    lng=lng,
                    place_id=None,
                    category=category,
                    distance_km=round(dist, 1) if dist is not None else None,
                ),
            )
        )
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:limit]]


def nearest_place_label(point: LatLng) -> str:
    best, best_d = None, float("inf")
    for name, address, lat, lng, _ in PUNE_PLACES:
        d = haversine_km(point.lat, point.lng, lat, lng)
        if d < best_d:
            best, best_d = (name, address), d
    if best and best_d < 0.4:
        return f"Near {best[0]}, {best[1]}"
    if best:
        return f"{best_d:.1f} km from {best[0]}, Pune"
    return f"{point.lat:.5f}, {point.lng:.5f}"
