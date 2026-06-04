import random

# A structured collection of high-converting video ad blueprints for BROOKSAUTOPLUG
VIDEO_ADS_COLLECTION = [
    {
        "title": "The Kampala Office Brake Rescue",
        "topic": "Mobile Brake Pad Replacement",
        "duration": "20 Seconds",
        "scenes": [
            {
                "time": "0-5s",
                "visual": "Close-up shot of a worn-out, squeaking brake pad being removed from a vehicle.",
                "voiceover": "That squeaking sound when you step on your brakes isn't just annoying—it's dangerous.",
                "text_overlay": "Brakes squeaking? 🛑"
            },
            {
                "time": "5-12s",
                "visual": "Camera pans out to show a professional BROOKSAUTOPLUG mechanic fixing the car right inside an office parking lot.",
                "voiceover": "Don't waste your productive working hours sitting at a garage. Our mobile mechanics come straight to your office or home.",
                "text_overlay": "We fix it at your office! 💼"
            },
            {
                "time": "12-20s",
                "visual": "A hand taps the 'Request Mobile Repair' button on your live website layout on a mobile phone.",
                "voiceover": "Visit brooksautoplug.com right now, log your location, and get a certified mechanic dispatched instantly.",
                "text_overlay": "Tap to book a mechanic! 📲\nbrooksautoplug.com"
            }
        ]
    },
    {
        "title": "The AI Luganda Mechanic Explainer",
        "topic": "AI Diagnostic Engine Promotion",
        "duration": "15 Seconds",
        "scenes": [
            {
                "time": "0-5s",
                "visual": "A driver looking confused inside a car while staring at a blinking engine warning light on the dashboard.",
                "voiceover": "Mmotoka yange eybuseeza taala naye tomanyi kigenda mumaaso?",
                "text_overlay": "Ebizibu bya Mmotoka? 😮"
            },
            {
                "time": "5-10s",
                "visual": "Screen recording of a user typing a car issue into the diagnostic box on your website using Luganda.",
                "voiceover": "Genda ku website yaffe, onyoozeemu ekizibu ky'ennyonnyola yo mu Luganda, AI yaffe ekuddemu mbulakayulu ey'enkomeredde.",
                "text_overlay": "Okozesa Oluganda oba English! 🧠"
            },
            {
                "time": "10-15s",
                "visual": "The AI generates the parts needed, and the user smoothly clicks 'Buy via WhatsApp'.",
                "voiceover": "Oluvanyuma landa ebyuma ebituufu ku WhatsApp yaffe mbulakayulu. Kola check-up leero ku brooksautoplug.com!",
                "text_overlay": "Free AI Diagnostics! 🌐\nbrooksautoplug.com"
            }
        ]
    }
]

def run_ad_generator():
    print("=========================================================")
    print("        BROOKSAUTOPLUG VIDEO AD PRODUCTION DESK          ")
    print("=========================================================\n")
    
    # Select a video blueprint blueprint to produce
    selected_ad = random.choice(VIDEO_ADS_COLLECTION)
    
    print(f"🎬 SELECTED CAMPAIGN: {selected_ad['title']}")
    print(f"📦 MARKETING FOCUS : {selected_ad['topic']}")
    print(f"⏱️ TARGET RUNTIME   : {selected_ad['duration']}\n")
    print("---------------------------------------------------------")
    print("           SECOND-BY-SECOND PRODUCTION GUIDE             ")
    print("---------------------------------------------------------")
    
    for idx, scene in enumerate(selected_ad['scenes'], 1):
        print(f"\n🎬 [SCENE {idx}] Timeframe: {scene['time']}")
        print(f"📸 CAMERA SHOT  : {scene['visual']}")
        print(f"🎙️ VOICE / AUDIO : \"{scene['voiceover']}\"")
        print(f"🔤 SCREEN TEXT  : [{scene['text_overlay'].replace('\n', ' | ')}]")
        print("-" * 55)

if __name__ == '__main__':
    run_ad_generator()