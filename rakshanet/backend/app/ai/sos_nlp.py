import re
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel


class SOSExtractionResult(BaseModel):
    original_message: str
    detected_language: str       # en, te, hi, ta, kn, ml
    language_name: str           # English, Telugu, Hindi, Tamil, Kannada, Malayalam
    is_transliterated: bool      # True if Roman script was used for an Indian language
    need_type: str               # medical, rescue, food, water, shelter, evacuation, other
    urgency: str                 # critical, high, medium, low
    priority_score: float        # 0.0 to 100.0
    people_count: Optional[int] = 1
    is_life_threatening: bool = False
    danger_factors: List[str] = []
    location_mentions: List[str] = []
    extracted_keywords: List[str] = []


class MultilingualSOSNLP:
    """
    Multilingual Natural Language Processing & Information Extraction Engine for RakshaNet.
    
    Supports:
    - English (en)
    - Telugu (te) (Native script + Transliterated/Latin script)
    - Hindi (hi) (Devanagari + Hinglish)
    - Tamil (ta) (Tamil script + Tanglish)
    - Kannada (kn) (Kannada script + Kanglish)
    - Malayalam (ml) (Malayalam script + Manglish)
    
    Operates 100% locally with zero external API dependencies or costs.
    """

    LANGUAGE_NAMES = {
        "en": "English",
        "te": "Telugu",
        "hi": "Hindi",
        "ta": "Tamil",
        "kn": "Kannada",
        "ml": "Malayalam"
    }

    # Transliteration keywords for Indian languages written in Roman script
    TRANSLITERATION_PATTERNS = {
        "te": [
            r"\b(neellu|neelu|neellu|vachayi|vachindi|maa|ammaku|mandulu|kavali|kapadandi|chikkukunnam|sahayam|illu|intloki|bhayanga|pillalu|aakali|paikappu)\b"
        ],
        "hi": [
            r"\b(paani|pani|ghar|mein|ghus|bachao|chhat|madad|dawa|dawai|fas|phase|doob|jaldi|turant|bacche|madat|bhookh|roti)\b"
        ],
        "ta": [
            r"\b(thanneer|tannir|veetukulle|veedu|kaapaatrunge|kaapathi|marundhu|udhavi|moolguthu|kudineer|kuzhandhai|pasikuthu)\b"
        ],
        "kn": [
            r"\b(neeru|maneyalli|mane|kaapadi|bachav|aushadhi|sahaya|hasivu|beku|silukikondiddeve|makkalu)\b"
        ],
        "ml": [
            r"\b(vellam|veettil|veedu|rakshikkanam|rakshikku|marunnu|sahayikku|sahayam|kuttikal|vishakkunnu)\b"
        ]
    }

    # Need Type Keyword dictionaries
    NEED_PATTERNS = {
        "medical": [
            # English & Medical terms
            r"\b(medicine|medicines|medical|doctor|insulin|pregnant|pregnancy|heart|cardiac|attack|bleeding|blood|stroke|asthma|inhaler|unconscious|fever|injury|injured|fracture|oxygen|dialysis|infant|baby|elderly|diabetic|diabetes|bp|sick|tablets|pills|injection)\b",
            # Hindi
            r"(दवा|दवाई|डॉक्टर|इंसुलिन|गर्भवती|दिल|खून|अस्पताल|बीमार|सांस|दर्द|चोट|ऑक्सीजन|डायलिसिस|बुजुर्ग)",
            # Telugu
            r"(మందులు|డాక్టర్|గర్భిణీ|ఇన్సులిన్|రక్తం|గుండె|ఆసుపత్రి|గాయం|జబ్బు|శ్వాస|చంటిపిల్ల|వృద్ధులు)",
            # Tamil
            r"(மருந்து|மருத்துவர்|இன்சுலின்|கர்ப்பிணி|காயம்|ரத்தம்|மருத்துவமனை|சுவாசம்|முதியவர்)",
            # Kannada
            r"(ಔಷಧಿ|ವೈದ್ಯರು|ಗರ್ಭಿಣಿ|ಇನ್ಸುಲಿನ್|ರಕ್ತ|ಆಸ್ಪತ್ರೆ|ಗಾಯ|ಉಸಿರಾಟ|ಹಿರಿಯರು)",
            # Malayalam
            r"(മരുന്ന്|ഡോക്ടർ|ഇൻസുലിൻ|ഗർഭിണി|രക്തം|ആശുപത്രി|മുറിവ്|ശ്വാസം|വൃദ്ധർ)",
            # Transliterated Indian language terms
            r"\b(mandulu|mandu|mandulani|dawa|dawai|marundhu|marunnu|aushadhi|aspatal|asupatri|maruthuvamanai)\b"
        ],
        "rescue": [
            # English
            r"\b(trapped|stuck|terrace|roof|rooftop|boat|drowning|drown|submerged|current|wash away|washed away|save us|help us|collapsing|stranded|marooned|water rising|rising fast)\b",
            # Hindi
            r"(फंसे|फंस|छत|नाव|डूब|डूबने|बचाओ|मदद|बाढ़|पानी बढ़|रेस्क्यू|बोट|धंस)",
            # Telugu
            r"(చిక్కుకున్నాము|చిక్కుకున్నాం|కాపాడండి|పైకప్పు|బోటు|మునిగిపోతోంది|మునుగు|రక్షించండి|నీళ్లు పెరుగుతున్నాయి|వరద)",
            # Tamil
            r"(மாட்டிகிட்டோம்|மாட்டிக்கொண்டோம்|காப்பாற்றுங்கள்|படகு|மாடி|மூழ்குகிறது|வெள்ளம்|உதவுங்கள்)",
            # Kannada
            r"(ಸಿಲುಕಿಕೊಂಡಿದ್ದೇವೆ|ಸಿಲುಕಿ|ಕಾಪಾಡಿ|ದೋಣಿ|ಮೇಲ್ಛಾವಣಿ|ಮುಳುಗುತ್ತಿದೆ|ಪ್ರವಾಹ|ಸಹಾಯ ಮಾಡಿ)",
            # Malayalam
            r"(കുടുങ്ങി|കുടുങ്ങിക്കിടക്കുന്നു|രക്ഷിക്കൂ|തോണി|മേൽക്കൂര|മുങ്ങുന്നു|വെള്ളപ്പൊക്കം|സഹായിക്കൂ)",
            # Transliterated terms
            r"\b(kapadandi|bachao|kaapaatrunge|kaapadi|rakshikku|chikkukunnam|phase|fas|doob|moolguthu|doni|thoni|boatu|naav)\b"
        ],
        "water": [
            # English
            r"\b(drinking water|potable water|bottled water|clean water|thirsty|dehydrated|dehydration)\b",
            # Hindi
            r"(पीने का पानी|स्वच्छ पानी|जल|प्यास)",
            # Telugu
            r"(తాగునీరు|మంచి నీళ్లు|దాహం|మంచినీరు)",
            # Tamil
            r"(குடிநீர்|தண்ணீர்|தாகம்)",
            # Kannada
            r"(ಕುಡಿಯುವ ನೀರು|ನೀರು|ಬಾಯಾರಿಕೆ)",
            # Malayalam
            r"(കുടിവെള്ളം|വെള്ളം|ദാഹം)",
            # Transliterated terms
            r"\b(kudineer|taaguneeru|peene ka pani|peene ka paani|manchi neellu)\b"
        ],
        "food": [
            # English
            r"\b(food|hungry|rations|starvation|groceries|baby milk|dry food|eating|biscuit|provisions)\b",
            # Hindi
            r"(खाना|भोजन|राशन|भूख|भूखे|दूध|बच्चों का खाना)",
            # Telugu
            r"(ఆహారం|భోజనం|పాలు|అన్నం|ఆకలి|చిరుతిండి)",
            # Tamil
            r"(உணவு|சாப்பாடு|பால்|பசி)",
            # Kannada
            r"(ಆಹಾರ|ಊಟ|ಹಾಲು|ಹಸಿವು)",
            # Malayalam
            r"(ഭക്ഷണം|ആഹാരം|പാൽ|വിശപ്പ്)",
            # Transliterated terms
            r"\b(aaharam|bhojan|khana|saappadu|unavu|oota|bhakshanam)\b"
        ],
        "evacuation": [
            # English
            r"\b(evacuate|evacuation|shift us|out of here|vehicle|transfer|nowhere to go|road blocked|cutoff|stranded)\b",
            # Hindi
            r"(बाहर निकालो|सुरक्षित स्थान|गाड़ी|रास्ता बंद|निकासी)",
            # Telugu
            r"(బయటకు తీయండి|తరలించండి|సురక్షిత ప్రాంతం|దారి మూసుకుపోయింది)",
            # Tamil
            r"(வெளியேற்றுங்கள்|வெளியே வர|பாதுகாப்பான இடம்)",
            # Kannada
            r"(ಹೊರಗೆ ಕರೆದೊಯ್ಯಿರಿ|ಸ್ಥಳಾಂತರಿಸಿ|ಸುರಕ್ಷಿತ ಸ್ಥಳ)",
            # Malayalam
            r"(ഒഴിപ്പിക്കുക|പുറത്തിറങ്ങാൻ|സുരക്ഷിത സ്ഥാനം)",
            # Transliterated terms
            r"\b(bayataku|nikalo|shift us|daari ledu|rasta band)\b"
        ],
        "shelter": [
            # English
            r"\b(shelter|roof blown|wall collapsed|house collapsed|relief camp|homeless)\b",
            # Hindi
            r"(आश्रय|छत उड़|दीवार गिर|मकान ढह|राहत शिविर)",
            # Telugu
            r"(ఆశ్రయం|నివాసం|గోడ కూలి|ఇల్లు కూలి|పునరావాస కేంద్రం)",
            # Tamil
            r"(தங்குமிடம்|அடைக்கலம்|சுவர் இடிந்து|முகாம்)",
            # Kannada
            r"(ಆಶ್ರಯ|ವಸತಿ|ಗೋಡೆ ಬಿದ್ದಿದೆ|ಶಿಬಿರ)",
            # Malayalam
            r"(അഭയം|താമസസ്ഥലം|മതിൽ ഇടിഞ്ഞു|ക്യാമ്പ്)"
        ]
    }

    LOCATION_PATTERNS = [
        # Building levels
        r"\b(ground floor|first floor|second floor|terrace|roof|rooftop|veranda|basement|attic)\b",
        r"(మొదటి అంతస్తు|పైకప్పు|గ్రౌండ్ ఫ్లోర్|మేడపై|బేస్మెంట్)",
        r"(भूतल|पहली मंजिल|छत|तहखाना)",
        r"(தரைத்தளம்|முதல் மாடி|மொட்டை மாடி)",
        r"(ನೆಲಮಾಳಿಗೆ|ಮೊದಲ ಮಹಡಿ|ಛಾವಣಿ)",
        r"(താഴത്തെ നില|ഒന്നാം നില|ടെറസ്സ്)",
        # Landmarks & Infrastructures
        r"\b(barrage|bund road|canal|sluice gate|underpass|flyover|bridge|junction|overpass|temple|hospital|school|college|workshop|shed|colony|ward|apartment|layout)\b",
        r"\b(krishnalanka|bhavanipuram|autonagar|gunadala|tadepalli|ramavarappadu|kanuru|poranki)\b",
        r"(కృష్ణలంక|భవానిపురం|ఆటోనగర్|గుణదల|తాడేపల్లి|రామవరప్పాడు|బ్యారేజీ|కాలువ|వంతెన)",
        r"(ऑटोनगर|भवानीपुरम|कृष्णालंका|गुणादला|ताडेपल्ली|पुल|नहर|बांध)",
        r"(பாலம்|அணை|கால்வாய்|கோவில்|மருத்துவமனை)"
    ]

    DANGER_PATTERNS = {
        "trapped_above_water": [
            r"\b(trapped|stuck on (roof|terrace|first floor)|water rising past)\b",
            r"(పైకప్పుపై చిక్కుకున్నాము|మొదటి అంతస్తు వరకు వచ్చింది)",
            r"(छत पर फंसे|पानी बढ़ रहा है)",
            r"(மாடியில் மாட்டிகிட்டோம்|மாட்டிகிட்டோம்|மாட்டிகொண்டோம்|மாட்டிகி|மாட்டிக்கொண்டோம்)",
            r"(ಮೇಲ್ಛಾವಣಿಯಲ್ಲಿ ಸಿಲುಕಿದ್ದೇವೆ|ಸಿಲುಕಿಕೊಂಡಿದ್ದೇವೆ)",
            r"(ടെറസ്സിൽ കുടുങ്ങി|കുടുങ്ങിക്കിടക്കുന്നു)"
        ],
        "critical_medical_emergency": [
            r"\b(insulin|heart attack|chest pain|bleeding heavily|dialysis|oxygen needed|unconscious|bp|diabetes|diabetic)\b",
            r"(ఇన్సులిన్ అత్యవసరం|గుండె జబ్బు|రక్తం కారుతోంది|బీపీ)",
            r"(इंसुलिन की तुरंत जरूरत|दिल का दौरा|खून बह रहा|बीपी)",
            r"(இன்சுலின் தேவை|மாரடைப்பு|பிபி)",
            r"(ಇನ್ಸುಲಿನ್ ತಕ್ಷಣ ಬೇಕು|ಹೃದಯಾಘಾತ|ಬಿಪಿ)",
            r"(ഇൻസുലിൻ വേണം|ഹൃദയാഘാതം|ബിപി)"
        ],
        "vulnerable_infant_or_pregnant": [
            r"\b(infant|baby|newborn|pregnant|labor pain|toddler)\b",
            r"(గర్భిణీ|చిన్న పిల్లలు|చంటిపాప|నవజాత శిశువు)",
            r"(गर्भवती|नवजात शिशु|छोटा बच्चा|प्रसव पीड़ा)",
            r"(கர்ப்பிணி|பச்சிளங்குழந்தை)",
            r"(ಗರ್ಭಿಣಿ|ಹಸುಗೂಸು|ಚಿಕ್ಕ ಮಗು)",
            r"(ഗർഭിണി|നവജാതശിശു|ചെറിയ കുട്ടി)"
        ],
        "rapid_flood_inundation": [
            r"\b(waist deep|neck deep|chest deep|water rising rapidly|swept away|submerged)\b",
            r"(నడుము లోతు|మెడ లోతు|వేగంగా పెరుగుతోంది|మునిగిపోయింది)",
            r"(कमर तक पानी|गले तक पानी|तेजी से बढ़ रहा|डूब रहा)",
            r"(இடுப்பளவு தண்ணீர்|வேகமாக உயர்கிறது)",
            r"(ಸೊಂಟದವರೆಗೆ ನೀರು|ವೇಗವಾಗಿ ಏರುತ್ತಿದೆ)",
            r"(അരയോളം വെള്ളം|വേഗത്തിൽ ഉയരുന്നു)"
        ],
        "hypothermia_or_isolation": [
            r"\b(power cut|electricity cut|freezing|darkness|no way out|cutoff|stranded)\b",
            r"(కరెంటు లేదు|చలి|ఎవరూ రాలేరు|దారి లేదు)",
            r"(बिजली गुल|अंधेरा|रास्ता कट गया)",
            r"(மின்சாரம் இல்லை|தனிமைப்படுத்தப்பட்டோம்)",
            r"(ಕರೆಂಟ್ ಇಲ್ಲ|ದಾರಿ ಮುಚ್ಚಿದೆ)",
            r"(കറന്റില്ല|വഴി അടഞ്ഞു)"
        ]
    }

    def detect_language(self, text: str) -> Tuple[str, str, bool]:
        """
        Detects primary language and whether transliteration was used.
        Uses character frequency majority voting across Indic Unicode scripts.
        Returns: (lang_code, language_name, is_transliterated)
        """
        # 1. Count characters across Indic Unicode scripts
        script_counts = {
            "te": sum(1 for c in text if "\u0c00" <= c <= "\u0c7f"),
            "hi": sum(1 for c in text if "\u0900" <= c <= "\u097f"),
            "ta": sum(1 for c in text if "\u0b80" <= c <= "\u0bff"),
            "kn": sum(1 for c in text if "\u0c80" <= c <= "\u0cff"),
            "ml": sum(1 for c in text if "\u0d00" <= c <= "\u0d7f")
        }
        dominant_script = max(script_counts, key=script_counts.get)
        if script_counts[dominant_script] > 0:
            return dominant_script, self.LANGUAGE_NAMES[dominant_script], False

        # 2. Check Romanized / Transliterated keywords
        text_lower = text.lower()
        for lang_code, patterns in self.TRANSLITERATION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower, re.IGNORECASE):
                    name = f"{self.LANGUAGE_NAMES[lang_code]} (Latin/Transliterated)"
                    return lang_code, name, True

        # Default to English
        return "en", self.LANGUAGE_NAMES["en"], False

    def extract_need_type(self, text: str) -> Tuple[str, List[str]]:
        """
        Classifies emergency need type and returns extracted trigger keywords.
        """
        text_lower = text.lower()
        detected_keywords = []

        # Check in priority order: medical, rescue, evacuation, water, food, shelter
        priority_order = ["medical", "rescue", "water", "food", "evacuation", "shelter"]

        for need in priority_order:
            patterns = self.NEED_PATTERNS[need]
            for pat in patterns:
                matches = re.findall(pat, text_lower, re.IGNORECASE)
                if matches:
                    flat_matches = [m if isinstance(m, str) else m[0] for m in matches]
                    detected_keywords.extend(flat_matches)
                    return need, list(set(detected_keywords))

        return "other", []

    def extract_people_count(self, text: str) -> int:
        """
        Extracts number of affected individuals from text.
        Handles numeric digits and natural language terms across languages.
        """
        text_lower = text.lower()

        # Regex for explicit numbers: e.g. "5 people", "4 लोग", "7 మందిమి", "6 members"
        count_match = re.search(
            r"\b(\d+)\s*(people|persons|members|family members|workers|kids|children|patients|लोग|व्यक्ति|మందిమి|మంది|సభ్యులు|பேர்|ಜನ|പേർ)?\b",
            text_lower
        )
        if count_match:
            try:
                num = int(count_match.group(1))
                if 1 <= num <= 500:
                    return num
            except ValueError:
                pass

        # Word numbers in English / Hindi / Telugu
        word_map = {
            "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
            "do": 2, "teen": 3, "char": 4, "paanch": 5, "chhah": 6, "saat": 7,
            "iddaru": 2, "mugguru": 3, "naluguru": 4, "aiduguru": 5, "aaruguru": 6,
            "family": 4, "infant": 2, "parents": 2
        }
        for word, val in word_map.items():
            if re.search(rf"\b{word}\b", text_lower):
                return val

        return 1

    def extract_danger_factors(self, text: str) -> Tuple[List[str], bool]:
        """
        Detects specific life-threatening danger triggers and returns danger factor list.
        """
        text_lower = text.lower()
        factors = []
        is_life_threatening = False

        for factor_name, patterns in self.DANGER_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower, re.IGNORECASE):
                    factors.append(factor_name)
                    if factor_name in ["trapped_above_water", "critical_medical_emergency", "vulnerable_infant_or_pregnant", "rapid_flood_inundation"]:
                        is_life_threatening = True
                    break

        return factors, is_life_threatening

    def extract_locations(self, text: str) -> List[str]:
        """
        Extracts spatial descriptors, flood levels, and landmark references.
        """
        text_lower = text.lower()
        locations = []
        for pat in self.LOCATION_PATTERNS:
            matches = re.findall(pat, text_lower, re.IGNORECASE)
            if matches:
                flat = [m if isinstance(m, str) else m[0] for m in matches if m]
                locations.extend(flat)
        return list(set(locations))

    def calculate_urgency_and_priority(
        self,
        need_type: str,
        is_life_threatening: bool,
        danger_factors: List[str],
        people_count: int,
        text: str
    ) -> Tuple[str, float]:
        """
        Computes calibrated urgency level and priority score (0-100).
        """
        text_lower = text.lower()
        urgent_words = [
            "urgent", "urgently", "immediately", "immediate", "emergency", "dying", "danger", "critical",
            "तुरंत", "आपातकालीन", "जल्दी", "बचाओ", "मदद",
            "వెంటనే", "అత్యవసరం", "కాపాడండి", "రక్షించండి",
            "உடனே", "உடனடியாக", "துரிதமாக", "காப்பாற்றுங்கள்", "காப்பாற்று",
            "ತುರ್ತು", "ತಕ್ಷಣ", "ಕಾಪಾಡಿ",
            "ഉടൻ", "അടിയന്തിരം", "രക്ഷിക്കൂ",
            "jaldi", "turant", "ventane", "kapadandi", "bachao"
        ]
        has_urgent_word = any(w in text_lower for w in urgent_words)

        # 1. Determine Urgency Level
        if is_life_threatening or (need_type in ["medical", "rescue"] and has_urgent_word):
            urgency = "critical"
        elif need_type in ["medical", "rescue"] or people_count >= 4 or has_urgent_word:
            urgency = "high"
        elif need_type in ["water", "food", "evacuation", "shelter"]:
            urgency = "high" if people_count >= 3 else "medium"
        else:
            urgency = "medium" if has_urgent_word else "low"

        # 2. Calibrated Priority Score
        base_scores = {
            "critical": 90.0,
            "high": 75.0,
            "medium": 52.0,
            "low": 30.0
        }
        score = base_scores[urgency]

        # Danger factors bonus (+2.5 pts each, max +10)
        score += min(10.0, len(danger_factors) * 2.5)

        # People count bonus (max +5)
        if people_count > 1:
            score += min(5.0, (people_count - 1) * 1.2)

        # Urgency word amplifier
        if has_urgent_word and urgency != "critical":
            score += 4.0

        return urgency, round(min(100.0, max(15.0, score)), 1)

    def process_sos(self, message: str) -> SOSExtractionResult:
        """
        Complete end-to-end NLP pipeline for a citizen SOS distress message.
        """
        clean_msg = message.strip()
        lang_code, lang_name, is_transliterated = self.detect_language(clean_msg)
        need_type, keywords = self.extract_need_type(clean_msg)
        people_count = self.extract_people_count(clean_msg)
        danger_factors, is_life_threatening = self.extract_danger_factors(clean_msg)
        locations = self.extract_locations(clean_msg)
        urgency, priority_score = self.calculate_urgency_and_priority(
            need_type=need_type,
            is_life_threatening=is_life_threatening,
            danger_factors=danger_factors,
            people_count=people_count,
            text=clean_msg
        )

        return SOSExtractionResult(
            original_message=clean_msg,
            detected_language=lang_code,
            language_name=lang_name,
            is_transliterated=is_transliterated,
            need_type=need_type,
            urgency=urgency,
            priority_score=priority_score,
            people_count=people_count,
            is_life_threatening=is_life_threatening,
            danger_factors=danger_factors,
            location_mentions=locations,
            extracted_keywords=keywords
        )


sos_nlp = MultilingualSOSNLP()
