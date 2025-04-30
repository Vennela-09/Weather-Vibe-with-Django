from django.shortcuts import render, redirect
import requests
import datetime
import time
from decouple import config

def home(request):
    # Use session to persist city and show_forecast states
    city = request.session.get('city', 'mangaluru')  # Default city
    searched_city = city  # Store the user-searched city
    show_forecast = request.session.get('show_forecast', False)
    error_message = None  # To store error message
    current_timestamp = int(time.time())  # Get current Unix timestamp

    if request.method == 'POST':
        if 'city' in request.POST:
            city = request.POST['city']
            searched_city = city
            # Reset show_forecast when searching for a new city
            show_forecast = False
            request.session['city'] = city
            request.session['show_forecast'] = show_forecast
            print(f"City updated to: {city}, show_forecast reset to: {show_forecast}")
        if 'toggle_forecast' in request.POST:
            # Toggle show_forecast
            show_forecast = not show_forecast
            request.session['show_forecast'] = show_forecast
            # Use the city from the session, not the form, to ensure consistency
            city = request.session.get('city', city)
            searched_city = city
            print(f"After toggle, city: {city}, show_forecast: {show_forecast}")

    # Load API keys from environment variables
    OPENWEATHERMAP_API_KEY = config('OPENWEATHERMAP_API_KEY')
    GOOGLE_API_KEY = config('GOOGLE_API_KEY')
    GOOGLE_SEARCH_ENGINE_ID = config('GOOGLE_SEARCH_ENGINE_ID')

    current_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}'
    forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHERMAP_API_KEY}'
    PARAMS = {'units': 'metric'}

    queries = [f"{city} 1920x1080", f"{city} cityscape", f"{city} landscape"]
    image_url = None

    for query in queries:
        city_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}&searchType=image&imgSize=xlarge"
        try:
            image_data = requests.get(city_url, timeout=10).json()
            print(f"Image API response for {city} with query '{query}': {image_data}")
            if 'items' in image_data and len(image_data['items']) > 0:
                for i in range(min(3, len(image_data['items']))):
                    try:
                        potential_url = image_data['items'][i]['link']
                        response = requests.head(potential_url, timeout=5)
                        if response.status_code == 200:
                            image_url = potential_url
                            print(f"Selected image URL for {city}: {image_url}")
                            break
                    except (requests.exceptions.RequestException, KeyError) as e:
                        print(f"Failed to access image {i} for {city}: {str(e)}")
                        continue
            if image_url:
                break
            else:
                print(f"No accessible image found in API response for {city} with query '{query}'")
        except (KeyError, requests.exceptions.RequestException) as e:
            print(f"Image API failed for {city} with query '{query}': {str(e)}")
            continue

    if not image_url:
        image_url = '/static/images/mangaluru.jpg'
        print(f"Falling back to local image for {city}: {image_url}")

    try:
        current_data = requests.get(current_url, params=PARAMS).json()
        description = current_data['weather'][0]['description']
        icon = current_data['weather'][0]['icon']
        temp = current_data['main']['temp']
        day = datetime.date.today()

        mood_map = {
            'clear sky': '☀️', 'few clouds': '🌤️', 'scattered clouds': '☁️',
            'broken clouds': '🌥️', 'overcast clouds': '☁️', 'light rain': '🌧️',
            'rain': '🌧️', 'thunderstorm': '⛈️', 'snow': '❄️'
        }
        mood_emoji = mood_map.get(description.lower(), '🌍')

        forecast_list = []
        if show_forecast:
            try:
                forecast_data = requests.get(forecast_url, params=PARAMS).json()
                print(f"Forecast API response for {city}: {forecast_data}")
                daily_forecasts = {}
                for item in forecast_data['list']:
                    forecast_date = datetime.datetime.fromtimestamp(item['dt']).date()
                    if forecast_date not in daily_forecasts:
                        daily_forecasts[forecast_date] = item
                    if len(daily_forecasts) == 5:
                        break
                for date, item in daily_forecasts.items():
                    forecast_list.append({
                        'time': date,
                        'temp': item['main']['temp'],
                        'description': item['weather'][0]['description'],
                        'icon': item['weather'][0]['icon']
                    })
                print(f"Forecast list for {city}: {forecast_list}")
            except Exception as e:
                print(f"Error fetching forecast data for {city}: {str(e)}")
                forecast_list = []

        context = {
            'description': description,
            'icon': icon,
            'temp': temp,
            'day': day,
            'city': city,
            'mood_emoji': mood_emoji,
            'exception_occurred': False,
            'error_message': error_message,
            'image_url': image_url,
            'forecast_list': forecast_list,
            'show_forecast': show_forecast,
            'current_timestamp': current_timestamp
        }

        if request.method == 'POST' and 'toggle_forecast' in request.POST and show_forecast:
            print(f"Redirecting to /#forecast with city: {city}, show_forecast: {show_forecast}")
            return redirect('/#forecast')

        return render(request, 'app/index.html', context)

    except (KeyError, requests.exceptions.RequestException):
        error_message = f"City '{searched_city}' not found. Showing weather for Mangaluru instead. Please try again."
        city = 'mangaluru'
        request.session['city'] = city  # Update session with fallback city
        current_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}'

        for query in queries:
            city_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}&searchType=image&imgSize=xlarge"
            try:
                image_data = requests.get(city_url, timeout=10).json()
                print(f"Image API response for Mangaluru with query '{query}': {image_data}")
                if 'items' in image_data and len(image_data['items']) > 0:
                    for i in range(min(3, len(image_data['items']))):
                        try:
                            potential_url = image_data['items'][i]['link']
                            response = requests.head(potential_url, timeout=5)
                            if response.status_code == 200:
                                image_url = potential_url
                                print(f"Selected image URL for Mangaluru: {image_url}")
                                break
                        except (requests.exceptions.RequestException, KeyError) as e:
                            print(f"Failed to access image {i} for Mangaluru: {str(e)}")
                            continue
                if image_url:
                    break
                else:
                    print(f"No accessible image found in API response for Mangaluru with query '{query}'")
            except (KeyError, requests.exceptions.RequestException) as e:
                print(f"Image API failed for Mangaluru with query '{query}': {str(e)}")
                continue

        if not image_url:
            image_url = '/static/images/mangaluru.jpg'
            print(f"Falling back to local image for Mangaluru: {image_url}")

        try:
            current_data = requests.get(current_url, params=PARAMS).json()
            description = current_data['weather'][0]['description']
            icon = current_data['weather'][0]['icon']
            temp = current_data['main']['temp']
            day = datetime.date.today()

            mood_map = {
                'clear sky': '☀️', 'few clouds': '🌤️', 'scattered clouds': '☁️',
                'broken clouds': '🌥️', 'overcast clouds': '☁️', 'light rain': '🌧️',
                'rain': '🌧️', 'thunderstorm': '⛈️', 'snow': '❄️'
            }
            mood_emoji = mood_map.get(description.lower(), '🌍')

            context = {
                'description': description,
                'icon': icon,
                'temp': temp,
                'day': day,
                'city': city,
                'mood_emoji': mood_emoji,
                'exception_occurred': True,
                'error_message': error_message,
                'image_url': image_url,
                'forecast_list': [],
                'show_forecast': show_forecast,
                'current_timestamp': current_timestamp
            }

            return render(request, 'app/index.html', context)

        except (KeyError, requests.exceptions.RequestException):
            error_message = f"City '{searched_city}' not found, and fallback data for Mangaluru could not be retrieved. Please try again."
            day = datetime.date.today()
            return render(request, 'app/index.html', {
                'description': 'clear sky',
                'icon': '01d',
                'temp': 28,
                'day': day,
                'city': 'mangaluru',
                'mood_emoji': '☀️',
                'exception_occurred': True,
                'error_message': error_message,
                'image_url': '/static/images/mangaluru.jpg',
                'forecast_list': [],
                'show_forecast': show_forecast,
                'current_timestamp': current_timestamp
            })