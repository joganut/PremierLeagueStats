import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Custom CSS for enhanced styling
def add_custom_css():
    st.markdown("""
        <style>
        body {
            background-color: #f7f9fc;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        .title {
            font-size: 3em;
            color: #1e90ff;  /* Dodger Blue */
            text-align: center;
            margin-bottom: 20px;
        }
        .subheader {
            font-size: 2em;
            color: #ff6347;  /* Tomato */
            text-align: center;
            margin-top: 20px;
        }
        .dataframe {
            font-family: 'Courier New', Courier, monospace;
        }
        .stButton>button {
            background-color: #1e90ff;
            color: white;
            font-size: 1.2em;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stSelectbox {
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def fetch_epl_data():
    url = "https://www.bbc.com/sport/football/premier-league/table"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching EPL data: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        st.error("🚫 Could not find the EPL table on the page.")
        return pd.DataFrame()

    headers = [header.text for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        table_data.append(cols)

    df = pd.DataFrame(table_data, columns=headers)
    if not df.empty:
        df = df.iloc[:, :-1]  # Remove the last column
    return df

@st.cache_data
def fetch_player_data():
    url = "https://www.bbc.com/sport/football/premier-league/top-scorers"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching player data: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        st.error("🚫 Could not find the player stats table on the page.")
        return pd.DataFrame()

    headers = [header.text for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        table_data.append(cols)

    df = pd.DataFrame(table_data, columns=headers)
    
    # Clean player names and separate them from teams
    def clean_column(value):
        return value[:len(value)//2]

    df['Name'] = df['Name'].apply(clean_column)

    df.drop_duplicates(inplace=True)  # Remove duplicate rows
    return df

@st.cache_data
def fetch_fixtures():
    url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching fixtures: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    fixtures = soup.find_all('div', class_='qa-match-block')

    fixtures_data = []
    for fixture in fixtures:
        date = fixture.find('h3').text.strip()
        matches = fixture.find_all('li', class_='gs-o-list-ui__item')
        for match in matches:
            teams = match.find_all('span', class_='gs-u-display-none gs-u-display-block@m qa-full-team-name')
            if teams:
                home_team = teams[0].text.strip()
                away_team = teams[1].text.strip()
                time = match.find('time').text.strip()
                fixtures_data.append([date, home_team, away_team, time])

    df = pd.DataFrame(fixtures_data, columns=['Date', 'Home Team', 'Away Team', 'Time'])
    return df

def main():
    add_custom_css()
    st.markdown('<div class="title">⚽ EPL Stats - 2024</div>', unsafe_allow_html=True)

    # Sidebar for navigation
    option = st.sidebar.selectbox("Choose a view", ["🏆 Team Stats", "🎯 Player Stats", "📅 Fixtures"])

    if option == "🏆 Team Stats":
        df = fetch_epl_data()

        if not df.empty:
            st.markdown('<div class="subheader">EPL Table - 2024</div>', unsafe_allow_html=True)
            
            # Search feature
            search_term = st.text_input("🔍 Search the table", "")
            if search_term:
                search_term = search_term.lower()
                df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

            st.dataframe(df)

    elif option == "🎯 Player Stats":
        df = fetch_player_data()

        if not df.empty:
            st.markdown('<div class="subheader">Top Scorers - 2024</div>', unsafe_allow_html=True)
            
            # Search feature
            search_term = st.text_input("🔍 Search the table", "")
            if search_term:
                search_term = search_term.lower()
                df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

            st.dataframe(df)

    elif option == "📅 Fixtures":
        df = fetch_fixtures()

        if not df.empty:
            st.markdown('<div class="subheader">Upcoming Fixtures</div>', unsafe_allow_html=True)
            st.dataframe(df)

if __name__ == "__main__":
    main()
