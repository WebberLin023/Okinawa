import csv
import json
import os
import urllib.parse
import base64

# 檔案對照
FILES = {
    "daily": "daily_info.csv",
    "itinerary": "itinerary.csv",
    "accommodation": "accommodation.csv",
    "packing": "packing.csv",
    "shopping": "shopping.csv",
    "car": "car_rental.csv",
    "weather": "weather.csv",
    "food": "food_map.csv",
    "churaumi": "churaumi.csv"
}

def read_csv(filename):
    if not os.path.exists(filename):
        print(f"警告：找不到 {filename}，將使用空資料。")
        return []
    
    # 嘗試多種編碼，解決 Windows Excel 存檔造成的編碼問題
    encodings = ['utf-8-sig', 'cp950', 'big5', 'utf-8']
    
    for enc in encodings:
        try:
            with open(filename, mode='r', encoding=enc) as f:
                reader = csv.DictReader(f)
                return [row for row in reader]
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"讀取 {filename} 時發生未預期的錯誤: {e}")
            return []
            
    print(f"嚴重錯誤：無法識別 {filename} 的編碼。請嘗試使用記事本開啟並另存為 UTF-8。")
    return []

def get_base64_image(filepath, fallback_url=""):
    """讀取圖片並轉為 Base64，若檔案不存在則回傳備用 URL"""
    if not os.path.exists(filepath):
        return fallback_url
    
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = os.path.splitext(filepath)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded_string}"
    except Exception as e:
        print(f"圖片轉換失敗 {filepath}: {e}")
        return fallback_url

def generate_html():
    print("🚀 正在讀取 CSV 資料並產生互動版網頁...")
    
    data = {key: read_csv(filename) for key, filename in FILES.items()}

    # --- 0. 圖片處理 (嵌入 Base64) ---
    print("📸 正在嵌入圖片...")
#    img_okinawa_map = get_base64_image("okinawa_map.jpg", "https://images.unsplash.com/photo-1542051841857-5f90071e7989?q=80&w=1200&auto=format&fit=crop")
    img_okinawa_map_2 = get_base64_image("okinawa_map_2.jpg", "https://placehold.co/800x400/e0f2fe/1e293b?text=Map+Route+Image")
    img_churaumi_map = get_base64_image("churaumi_map.jpg", "https://placehold.co/800x400/e2e8f0/64748b?text=Please+Add+churaumi_map.jpg")
    img_churaumi_timetable = get_base64_image("churaumi_timetable.png", "") # 無備用圖，直接隱藏

    # --- 1. 資料處理：美食 ---
    meal_options = {}
    extra_food = []
    all_food_list = []
    food_categories = set()

    for row in data['food']:
        slot = row.get('slot', '').strip()
        query = row.get('map_query', row['name'])
        map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"
        category = row['category']
        food_categories.add(category)
        
        food_item = {
            "name": row['name'],
            "category": category,
            "desc": row['desc'],
            "dayInfo": row['day_info'],
            "mapUrl": map_url,
            "slot": slot
        }
        all_food_list.append(food_item)
        if slot:
            if slot not in meal_options: meal_options[slot] = []
            meal_options[slot].append(food_item)
        else:
            extra_food.append(food_item)

    sorted_categories = ["全部"] + sorted(list(food_categories))
    
    # --- 2. 資料處理：行程 ---
    days_json = []
    for day_info in data['daily']:
        day_id = day_info['day_id']
        day_events = [e for e in data['itinerary'] if e['day_id'] == day_id]
        events_formatted = []
        for ev in day_events:
            map_query = urllib.parse.quote(ev['title'])
            map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
            events_formatted.append({
                "time": ev['time'], "icon": ev['icon'], "tag": ev['tag'],
                "title": ev['title'], "desc": ev['desc'], "note": ev['note'],
                "planB": ev['plan_b'], "slot": ev.get('slot', ''), "mapUrl": map_url
            })
        days_json.append({
            "id": day_id, "date": day_info['date'],
            "theme": day_info['theme'], "rainPlan": day_info['rain_plan'],
            "events": events_formatted
        })

    # --- 3. 資料處理：總表 ---
    full_table_raw = []
    date_map = {d['day_id']: d['date'] for d in data['daily']}
    for ev in data['itinerary']:
        map_query = urllib.parse.quote(ev['title'])
        map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
        full_table_raw.append({
            "day": date_map.get(ev['day_id'], ev['day_id']),
            "time": ev['time'], "title": ev['title'], "tag": ev['tag'],
            "desc": ev['desc'], "note": ev['note'], "planB": ev['plan_b'],
            "slot": ev.get('slot', ''), "mapUrl": map_url
        })

    # --- 4. 資料處理：美麗海 ---
    churaumi_shows = [r for r in data.get('churaumi', []) if r['type'] == 'show']
    churaumi_tips = [r for r in data.get('churaumi', []) if r['type'] != 'show']

    # --- 5. 資料處理：其他 ---
    # 住宿 HTML
    acc_html = '<div class="grid gap-6 md:grid-cols-3">'
    for row in data['accommodation']:
        hotel_map = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(row['name'])}"
        nearby_tags = "".join([f'<span class="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-1 rounded-md">{t.strip()}</span>' for t in row['nearby'].split('|')])
        acc_html += f'''
            <div class="bg-white p-4 rounded-xl border border-indigo-100 shadow-sm flex flex-col">
                <div class="mb-3"><span class="text-xs font-bold text-white bg-indigo-500 px-3 py-1 rounded-full">{row['day_range']}</span></div>
                <h3 class="font-bold text-slate-800 text-lg mb-1">{row['name']}</h3>
                <p class="text-xs text-slate-500 mb-2"><i data-lucide="map-pin" class="w-3 h-3 inline"></i> {row['location']}</p>
                <div class="bg-slate-50 p-2 rounded text-xs text-slate-600 mb-2 space-y-1">
                    <div>📍 {row.get('address','')}</div><div>📞 {row.get('phone','')}</div>
                </div>
                <p class="text-sm text-slate-600 mb-3 flex-grow">{row['features']}</p>
                <div class="border-t pt-2 flex flex-wrap gap-1">{nearby_tags}</div>
                <a href="{hotel_map}" target="_blank" class="mt-3 text-center block w-full py-2 bg-indigo-50 text-indigo-600 text-xs font-bold rounded hover:bg-indigo-100">查看地圖</a>
            </div>'''
    acc_html += '</div>'

    # 清單 JSON
    packing_grouped = {}
    for item in data['packing']:
        cat = item['category']
        if cat not in packing_grouped: packing_grouped[cat] = []
        packing_grouped[cat].append({"item": item['item'], "note": item.get('note', '')})
    
    shopping_json_list = []
    for row in data['shopping']:
        shopping_json_list.append({"location": row['location'], "desc": row['desc'], "items": [i.strip() for i in row['item'].split('|')]})

    # 序列化 JSON 供 JS 使用
    # 這裡直接使用 list/dict 物件，解決 NameError 問題
    js_data = {
        "daysDataRaw": json.dumps(days_json, ensure_ascii=False),
        "mealOptions": json.dumps(meal_options, ensure_ascii=False),
        "extraFood": json.dumps(extra_food, ensure_ascii=False),
        "allFoodList": json.dumps(all_food_list, ensure_ascii=False),
        "foodCategories": json.dumps(sorted_categories, ensure_ascii=False), # 修正: 使用 sorted_categories
        "packingData": json.dumps([{"category": k, "items": v} for k, v in packing_grouped.items()], ensure_ascii=False),
        "shoppingData": json.dumps(shopping_json_list, ensure_ascii=False),
        "carData": json.dumps(data['car'], ensure_ascii=False),
        "weatherData": json.dumps(data['weather'], ensure_ascii=False),
        "fullTableRaw": json.dumps(full_table_raw, ensure_ascii=False),
        "churaumiShows": json.dumps(churaumi_shows, ensure_ascii=False),
        "churaumiTips": json.dumps(churaumi_tips, ensure_ascii=False)
    }

    # --- HTML 樣板 (拆分以避免 f-string 錯誤) ---
    
    html_head = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🌊 沖繩親子自駕攻略 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Zen+Maru+Gothic:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Zen Maru Gothic', 'Noto Sans TC', sans-serif; background-color: #f8fafc; color: #334155; padding-bottom: 80px; }
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .tag { font-size: 0.7rem; padding: 2px 8px; border-radius: 6px; font-weight: bold; white-space: nowrap; }
        .tag-food { background: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
        .tag-traffic { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }
        .tag-spot { background: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; }
        .tag-shop { background: #fdf2f8; color: #be185d; border: 1px solid #fbcfe8; }
        .tag-nap { background: #faf5ff; color: #7e22ce; border: 1px solid #d8b4fe; }
        .tag-hotel { background: #fdf4ff; color: #86198f; border: 1px solid #f0abfc; }
        .tag-park { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .nav-btn { position: relative; color: #64748b; font-weight: 500; padding: 0.5rem 1rem; transition: color 0.2s; }
        .nav-btn.active { color: #0ea5e9; font-weight: 700; }
        .nav-btn.active::after { content: ''; position: absolute; bottom: -2px; left: 0; right: 0; height: 3px; background-color: #0ea5e9; border-radius: 99px; }
        .fade-in { animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .meal-radio:checked + div { border-color: #f97316; background-color: #fff7ed; box-shadow: 0 0 0 1px #f97316; }
        .meal-radio:checked + div .check-icon { opacity: 1; transform: scale(1); }
        .filter-btn.active { background-color: #f97316; color: white; border-color: #f97316; }
        .hero-img { width: 100%; height: auto; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 20px; object-fit: cover; }
    </style>
</head>"""

    html_body_start = """
<body class="bg-slate-50">
    <nav class="sticky top-0 z-50 bg-white/90 backdrop-blur-md shadow-sm border-b border-slate-200">
        <div class="max-w-4xl mx-auto px-4">
            <div class="flex items-center justify-between h-14">
                <h1 class="text-lg font-bold text-slate-800 flex items-center gap-2"><span class="bg-blue-500 text-white p-1 rounded-md"><i data-lucide="plane" width="16"></i></span> 沖繩自駕趣</h1>
                <div class="text-xs text-slate-500 font-mono">2026.07.19-25</div>
            </div>
            <div class="flex overflow-x-auto hide-scrollbar -mx-4 px-4 pb-1 gap-2 text-sm whitespace-nowrap">
                <button onclick="switchTab('dashboard')" class="nav-btn active" data-tab="dashboard">總覽</button>
                <button onclick="switchTab('days')" class="nav-btn" data-tab="days">每日行程</button>
                <button onclick="switchTab('churaumi')" class="nav-btn text-cyan-600" data-tab="churaumi">🐋 美麗海</button>
                <button onclick="switchTab('foodmap')" class="nav-btn text-pink-600" data-tab="foodmap">美食地圖</button>
                <button onclick="switchTab('planner')" class="nav-btn text-orange-600" data-tab="planner">餐廳排程</button>
                <button onclick="switchTab('hotel')" class="nav-btn" data-tab="hotel">住宿交通</button>
                <button onclick="switchTab('prep')" class="nav-btn" data-tab="prep">行前準備</button>
                <button onclick="switchTab('fulltable')" class="nav-btn" data-tab="fulltable">總表</button>
            </div>
        </div>
    </nav>

    <main id="content-area" class="max-w-4xl mx-auto p-4 min-h-[80vh]"></main>

    <footer class="text-center py-8 text-slate-400 text-xs">
        <p>Made for 沖繩 7天6夜 親子自駕行</p>
    </footer>
"""

    # JS 部分，使用 f-string 填入資料，注意 JS 的大括號需雙倍 {{ }}
    html_script = f"""
    <script>
        const accContent = `{acc_html}`;
        const daysDataRaw = {js_data['daysDataRaw']};
        const mealOptions = {js_data['mealOptions']};
        const extraFood = {js_data['extraFood']};
        const allFoodList = {js_data['allFoodList']};
        const foodCategories = {js_data['foodCategories']};
        const packingData = {js_data['packingData']};
        const shoppingData = {js_data['shoppingData']};
        const carData = {js_data['carData']};
        const weatherData = {js_data['weatherData']};
        const fullTableRaw = {js_data['fullTableRaw']};
        const churaumiShows = {js_data['churaumiShows']};
        const churaumiTips = {js_data['churaumiTips']};

        const selectedMeals = {{}};
        for (const [slot, options] of Object.entries(mealOptions)) {{
            if (options.length > 0) selectedMeals[slot] = 0; 
        }}

        const contentArea = document.getElementById('content-area');
        const navBtns = document.querySelectorAll('.nav-btn');

        function switchTab(tabId) {{
            navBtns.forEach(btn => btn.classList.remove('active'));
            const activeBtn = document.querySelector(`.nav-btn[data-tab="${{tabId}}"]`);
            if (activeBtn) activeBtn.classList.add('active');
            
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
            contentArea.innerHTML = '';
            
            if (tabId === 'dashboard') renderDashboard();
            else if (tabId === 'days') renderDaysView();
            else if (tabId === 'churaumi') renderChuraumi();
            else if (tabId === 'foodmap') renderFoodMap();
            else if (tabId === 'planner') renderMealPlanner();
            else if (tabId === 'hotel') renderHotelTraffic();
            else if (tabId === 'prep') renderPreparation();
            else if (tabId === 'fulltable') renderFullTable();
            lucide.createIcons();
        }}

        function getEventDisplayData(ev) {{
            if (ev.slot && mealOptions[ev.slot]) {{
                const selectedIdx = selectedMeals[ev.slot] || 0;
                const meal = mealOptions[ev.slot][selectedIdx];
                const backups = mealOptions[ev.slot]
                    .filter((_, idx) => idx !== selectedIdx)
                    .map(m => m.name)
                    .join(' / ');
                return {{ title: meal.name, desc: meal.desc, planB: backups || ev.planB, mapUrl: meal.mapUrl, note: ev.note }};
            }}
            return ev;
        }}

        function renderChuraumi() {{
            let html = `<div class="fade-in space-y-8">`;
            html += `<div><h2 class="font-bold text-slate-800 mb-3 text-xl flex items-center gap-2"><i data-lucide="fish" class="text-cyan-500"></i> 美麗海水族館攻略</h2><img src="{img_churaumi_map}" alt="美麗海園區地圖" class="hero-img" onerror="this.src='https://placehold.co/800x400/e2e8f0/64748b?text=Please+Add+churaumi_map.jpg';"></div>`;
            html += `<div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-5"><h3 class="font-bold text-lg text-slate-700 mb-4 flex items-center gap-2"><i data-lucide="clock" class="text-blue-500"></i> 表演時刻表</h3><img src="{img_churaumi_timetable}" alt="表演時間表" class="w-full h-auto rounded-lg mb-6 border border-slate-200" onerror="this.style.display='none'"><div class="space-y-4">`;
            churaumiShows.forEach(show => {{
                html += `<div class="flex gap-4 border-b border-slate-50 pb-3 last:border-0 last:pb-0"><div class="text-blue-600 font-mono font-bold text-lg min-w-[50px]">${{show.time}}</div><div><div class="font-bold text-slate-800">${{show.title}}</div><p class="text-sm text-slate-500 mt-1">${{show.desc}}</p></div></div>`;
            }});
            html += `</div></div>`;

            html += `<div class="bg-cyan-50 rounded-2xl border border-cyan-100 p-5"><h3 class="font-bold text-lg text-cyan-800 mb-4 flex items-center gap-2"><i data-lucide="lightbulb" class="text-cyan-600"></i> 達人筆記</h3><div class="space-y-3">`;
            churaumiTips.forEach(tip => {{
                html += `<div class="flex gap-3 items-start"><i data-lucide="check-circle" class="w-5 h-5 text-cyan-500 shrink-0 mt-0.5"></i><div class="text-sm text-cyan-900 leading-relaxed"><span class="font-bold block mb-1">${{tip.title.replace('✅ ', '')}}</span>${{tip.desc}}</div></div>`;
            }});
            html += `</div></div></div>`;
            
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}

        function renderFoodMap() {{
            let html = `<div class="fade-in space-y-6">`;
            html += `<div class="sticky top-[110px] bg-slate-50/95 backdrop-blur z-30 py-2 -mx-4 px-4 border-b border-slate-200 flex gap-2 overflow-x-auto hide-scrollbar">`;
            foodCategories.forEach(cat => {{ html += `<button onclick="filterFood('${{cat}}')" class="filter-btn px-4 py-1.5 rounded-full bg-white border border-slate-200 text-sm font-bold text-slate-600 whitespace-nowrap transition-all ${{cat==='全部'?'active':''}}">${{cat}}</button>`; }});
            html += `</div><div id="food-grid" class="grid gap-4 sm:grid-cols-2">`;
            allFoodList.forEach(food => {{ html += `<div class="food-card bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-col group hover:shadow-md transition-all" data-cat="${{food.category}}"><div class="flex justify-between items-start mb-2"><div><span class="text-[10px] font-bold text-slate-400 uppercase tracking-wide block mb-1">${{food.category}}</span><h3 class="font-bold text-lg text-slate-800 group-hover:text-pink-600 transition-colors">${{food.name}}</h3></div>${{food.dayInfo ? `<span class="text-xs bg-slate-100 px-2 py-1 rounded text-slate-500 font-mono whitespace-nowrap">${{food.dayInfo}}</span>` : ''}}</div><p class="text-sm text-slate-600 mb-4 flex-grow leading-relaxed">${{food.desc}}</p><a href="${{food.mapUrl}}" target="_blank" class="w-full mt-auto py-2 rounded-lg bg-pink-50 text-pink-600 text-sm font-bold flex items-center justify-center gap-2 hover:bg-pink-100 transition-colors"><i data-lucide="map-pin" width="14"></i> Google Maps</a></div>`; }});
            html += `</div></div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}

        window.filterFood = function(category) {{
            document.querySelectorAll('.filter-btn').forEach(btn => {{ if(btn.innerText === category) {{ btn.classList.add('active'); }} else {{ btn.classList.remove('active'); }} }});
            document.querySelectorAll('.food-card').forEach(card => {{ card.style.display = (category === '全部' || card.dataset.cat === category) ? 'flex' : 'none'; }});
        }}

        function renderMealPlanner() {{
            let html = `<div class="fade-in space-y-8"><div class="bg-orange-50 p-4 rounded-xl border border-orange-100 text-orange-800 text-sm"><i data-lucide="info" class="inline w-4 h-4 mr-1"></i> 在此勾選您想吃的餐廳，<strong>每日行程</strong>與<strong>詳細總表</strong>會自動更新！</div>`;
            const sortedSlots = Object.keys(mealOptions).sort();
            sortedSlots.forEach(slot => {{
                const options = mealOptions[slot];
                const dayLabel = options[0].dayInfo || slot; 
                html += `<div class="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden"><div class="bg-slate-50 px-4 py-3 border-b border-slate-100 font-bold text-slate-700 flex items-center gap-2"><span class="bg-white border border-slate-200 px-2 py-0.5 rounded text-xs text-slate-500 font-mono">${{slot}}</span>${{dayLabel}}</div><div class="p-4 space-y-3">`;
                options.forEach((opt, idx) => {{
                    const isChecked = (selectedMeals[slot] === idx) ? 'checked' : '';
                    html += `<label class="block relative cursor-pointer group"><input type="radio" name="${{slot}}" value="${{idx}}" class="peer sr-only meal-radio" ${{isChecked}} onchange="updateMeal('${{slot}}', ${{idx}})"><div class="p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-all flex items-start gap-3"><div class="w-5 h-5 rounded-full border border-slate-300 flex items-center justify-center bg-white peer-checked:border-orange-500 peer-checked:bg-orange-500 mt-0.5 shrink-0"><div class="w-2 h-2 rounded-full bg-white opacity-0 check-icon transition-opacity"></div></div><div class="flex-1"><div class="flex justify-between items-start"><h4 class="font-bold text-slate-800 text-sm">${{opt.name}}</h4><span class="text-[10px] bg-slate-100 text-slate-500 px-1.5 rounded">${{opt.category}}</span></div><p class="text-xs text-slate-500 mt-1">${{opt.desc}}</p></div></div></label>`;
                }});
                html += `</div></div>`;
            }});
            html += `<h3 class="font-bold text-lg text-slate-700 mt-8 mb-4">✨ 更多推薦 (口袋名單)</h3><div class="grid gap-3 sm:grid-cols-2">`;
            extraFood.forEach(food => {{ html += `<div class="bg-white p-3 rounded-xl border border-slate-100 flex gap-3 items-center"><div class="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-pink-500 font-bold text-xs shrink-0">推</div><div><div class="font-bold text-sm text-slate-800">${{food.name}}</div><div class="text-xs text-slate-500">${{food.desc}}</div></div></div>`; }});
            html += `</div></div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}

        window.updateMeal = function(slot, index) {{ selectedMeals[slot] = index; }}

        function renderDaysView() {{
            let html = `<div class="fade-in space-y-8">`;
            html += `<div class="flex gap-2 overflow-x-auto hide-scrollbar pb-2 sticky top-[110px] bg-[#f8fafc] z-40 py-2">`;
            daysDataRaw.forEach((day, idx) => {{ html += `<button onclick="document.getElementById('day-${{day.id}}').scrollIntoView({{behavior:'smooth', block:'center'}})" class="px-4 py-1.5 rounded-full bg-white border border-slate-200 text-sm font-bold text-slate-600 shadow-sm whitespace-nowrap hover:bg-blue-50 hover:text-blue-600 transition-colors">D${{idx+1}} ${{day.theme}}</button>`; }});
            html += `</div>`;
            daysDataRaw.forEach((day, idx) => {{
                html += `<div id="day-${{day.id}}" class="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden scroll-mt-32"><div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex justify-between items-center"><div><span class="text-xs font-bold text-blue-500 uppercase tracking-wider">Day ${{idx+1}}</span><h2 class="text-xl font-bold text-slate-800">${{day.date}}</h2></div><div class="text-right"><div class="text-sm font-bold text-slate-600">${{day.theme}}</div></div></div><div class="bg-blue-50/50 px-6 py-3 border-b border-blue-100/50 flex gap-3 text-sm text-blue-800"><i data-lucide="cloud-rain" class="w-4 h-4 shrink-0 mt-0.5"></i><span>${{day.rainPlan}}</span></div><div class="p-6 relative">`;
                day.events.forEach((ev, eIdx) => {{
                    const displayData = getEventDisplayData(ev);
                    const isLast = eIdx === day.events.length - 1;
                    const isNap = ev.tag === 'nap';
                    html += `<div class="flex gap-4 relative group">${{!isLast ? '<div class="absolute left-[19px] top-8 bottom-[-32px] w-[2px] bg-slate-100 group-hover:bg-blue-100 transition-colors"></div>' : ''}}<div class="flex flex-col items-center min-w-[50px] z-10"><span class="text-[10px] font-bold font-mono mb-1 text-slate-400">${{ev.time}}</span><div class="w-10 h-10 rounded-full flex items-center justify-center ${{isNap ? 'bg-purple-100 text-purple-600 ring-4 ring-purple-50' : 'bg-white border border-slate-200 text-slate-500 group-hover:border-blue-300 group-hover:text-blue-500'}} transition-all shadow-sm"><i data-lucide="${{ev.icon}}" width="18"></i></div></div><div class="flex-1 pb-8"><div class="${{isNap ? 'bg-purple-50 border-purple-100' : 'bg-white border-slate-100 hover:border-blue-200'}} border rounded-2xl p-4 transition-all shadow-sm"><div class="flex justify-between items-start mb-2"><h3 class="font-bold text-lg text-slate-800">${{displayData.title}}</h3><span class="tag tag-${{ev.tag}}">${{getTagLabel(ev.tag)}}</span></div><p class="text-sm text-slate-600 leading-relaxed mb-3">${{displayData.desc}}</p><div class="flex flex-wrap gap-2">${{displayData.planB ? `<span class="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded border border-amber-100 flex items-center gap-1"><i data-lucide="info" width="12"></i>備案：${{displayData.planB}}</span>` : ''}}${{displayData.note ? `<span class="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded flex items-center gap-1"><i data-lucide="sticky-note" width="12"></i> ${{displayData.note}}</span>` : ''}}<a href="${{displayData.mapUrl}}" target="_blank" class="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded border border-blue-100 flex items-center gap-1 hover:bg-blue-100 transition-colors ml-auto"><i data-lucide="map-pin" width="12"></i> 導航</a></div></div></div></div>`;
                }});
                html += `</div></div>`;
            }});
            html += `</div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}

        function renderFullTable() {{
            let html = `<div class="fade-in bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"><div class="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center"><h2 class="font-bold text-slate-700">📋 行程詳細總表 (動態更新)</h2></div><div class="overflow-x-auto"><table class="w-full text-sm text-left text-slate-500"><thead class="text-xs text-slate-700 uppercase bg-slate-50"><tr><th class="px-4 py-3">Day</th><th class="px-4 py-3">時間</th><th class="px-4 py-3">活動</th><th class="px-4 py-3">詳細說明</th><th class="px-4 py-3">備案</th></tr></thead><tbody>`;
            fullTableRaw.forEach(row => {{
                const displayData = getEventDisplayData(row);
                html += `<tr class="bg-white border-b hover:bg-slate-50"><td class="px-4 py-3 font-medium text-slate-900 whitespace-nowrap">${{row.day}}</td><td class="px-4 py-3 font-mono">${{row.time}}</td><td class="px-4 py-3 font-bold text-slate-800">${{displayData.title}}</td><td class="px-4 py-3 min-w-[200px]">${{displayData.desc}}</td><td class="px-4 py-3 text-xs text-amber-600">${{displayData.planB || '-'}}</td></tr>`;
            }});
            html += `</tbody></table></div></div>`;
            contentArea.innerHTML = html;
        }}

        function renderDashboard() {{
            let html = `<div class="fade-in space-y-8">`;
            // 航班 & 天氣
            html += `<div class="grid grid-cols-1 md:grid-cols-2 gap-4"><div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm"><h3 class="font-bold text-slate-700 mb-3 flex items-center gap-2"><i data-lucide="plane" class="text-blue-500"></i> 航班資訊</h3><div class="flex justify-between items-center border-b border-slate-50 pb-2 mb-2"><span class="text-xs text-slate-400">去程 7/19</span><span class="font-bold text-slate-800">14:25 抵達</span></div><div class="flex justify-between items-center"><span class="text-xs text-slate-400">回程 7/25</span><span class="font-bold text-slate-800">15:35 起飛</span></div></div><div class="bg-orange-50 p-5 rounded-2xl border border-orange-100"><h3 class="font-bold text-orange-800 mb-3 flex items-center gap-2"><i data-lucide="sun" class="text-orange-500"></i> 7月天氣概況</h3><div class="text-sm text-orange-700 space-y-1"><p>🌡️ 27°C - 32°C</p><p>👕 穿著建議：短袖、透氣材質</p><p>☂️ 注意事項：午後雷陣雨、室內冷氣強</p></div></div></div>`;
            // 插畫 & 地圖
            html += `<div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm"><h2 class="font-bold text-slate-700 mb-3 text-lg flex items-center gap-2"><i data-lucide="navigation" class="text-green-500"></i> 路線地圖</h2><img src="{img_okinawa_map_2}" alt="沖繩路線地圖" class="w-full h-auto rounded-xl" onerror="this.src='https://placehold.co/800x400/e0f2fe/1e293b?text=Map+Route'"></div>`;
            html += `</div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}

        // (其他功能函式保持不變: renderHotelTraffic, renderPreparation, getTagLabel)
        function renderHotelTraffic() {{
            let html = `<div class="fade-in space-y-8"><div><h2 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><i data-lucide="bed" class="text-indigo-500"></i> 住宿安排</h2>${{accContent}}</div><div><h2 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><i data-lucide="car" class="text-blue-500"></i> 租車資訊</h2><div class="grid gap-4 sm:grid-cols-2">`;
            carData.forEach(row => {{ html += `<div class="bg-white p-4 rounded-xl border border-slate-100 shadow-sm"><span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">${{row.category}}</span><h3 class="font-bold text-slate-700 mb-2">${{row.title}}</h3><p class="text-sm text-slate-600 leading-relaxed">${{row.details}}</p></div>`; }});
            html += `</div></div></div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}
        function renderPreparation() {{
            let html = `<div class="fade-in space-y-8"><div><h2 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><i data-lucide="backpack" class="text-purple-500"></i> 攜帶物品</h2><div class="grid gap-4 sm:grid-cols-2">`;
            packingData.forEach(cat => {{ html += `<div class="bg-white p-5 rounded-2xl border border-purple-50 shadow-sm"><h3 class="font-bold text-purple-700 mb-3 border-b border-purple-50 pb-2">${{cat.category}}</h3><ul class="space-y-3">${{cat.items.map(i => `<li class="checklist-item flex items-start gap-3"><input type="checkbox" class="mt-1 w-4 h-4 accent-purple-600 rounded border-slate-300 cursor-pointer"><div class="flex-1"><span class="text-sm text-slate-700 font-medium block">${{i.item}}</span>${{i.note ? `<span class="text-xs text-slate-400">${{i.note}}</span>` : ''}}</div></li>`).join('')}}</ul></div>`; }});
            html += `</div></div><div><h2 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><i data-lucide="shopping-bag" class="text-pink-500"></i> 購物攻略</h2><div class="space-y-4">`;
            shoppingData.forEach(shop => {{ html += `<div class="bg-white p-5 rounded-2xl border border-pink-50 shadow-sm flex flex-col sm:flex-row gap-4"><div class="sm:w-1/3 border-b sm:border-b-0 sm:border-r border-pink-50 pb-3 sm:pb-0 sm:pr-4"><h3 class="font-bold text-pink-700 text-lg">${{shop.location}}</h3><p class="text-sm text-slate-500 mt-1">${{shop.desc}}</p></div><div class="flex-1"><div class="flex flex-wrap gap-2">${{shop.items.map(i => `<span class="bg-pink-50 text-pink-700 text-xs px-2.5 py-1 rounded-md border border-pink-100 flex items-center gap-1"><i data-lucide="check" width="10"></i> ${{i}}</span>`).join('')}}</div></div></div>`; }});
            html += `</div></div></div>`;
            contentArea.innerHTML = html;
            lucide.createIcons();
        }}
        function getTagLabel(tag) {{ const map = {{ food: "美食", traffic: "交通", spot: "景點", shop: "購物", nap: "午睡/休息", hotel: "住宿", park: "公園/放電" }}; return map[tag] || "其他"; }}

        switchTab('dashboard');
    </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        # 修正：將所有 HTML 區塊組合起來寫入
        f.write(html_head + html_body_start + html_script)
    
    print("✅ 互動版 index.html 已生成！")

if __name__ == "__main__":
    generate_html()