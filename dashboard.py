import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimalist CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 300;
        letter-spacing: -0.5px;
    }
    .section-header {
        font-size: 1.2rem;
        color: #2c3e50;
        margin: 1.5rem 0 0.5rem 0;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .city-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .temperature-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .weather-description {
        font-size: 0.9rem;
        color: #7f8c8d;
        text-transform: capitalize;
    }
    .download-button {
        background-color: #3498db;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
    .download-button:hover {
        background-color: #2980b9;
    }
    .dataset-table {
        font-size: 0.9rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


class WeatherDashboard:
    def __init__(self):
        self.df = self.load_data()
        self.cities_order = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Kolkata",
                             "Hyderabad", "Jaipur", "Pune", "Ghaziabad"]

    def load_data(self):
        """Load weather data from SQLite database"""
        try:
            with sqlite3.connect("weather_data.db") as conn:
                df = pd.read_sql_query("SELECT * FROM weather_log", conn)
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
            df['load_timestamp_utc'] = pd.to_datetime(df['load_timestamp_utc'])
            return df
        except:
            return pd.DataFrame()

    def get_latest_data(self):
        """Compute latest weather data per city"""
        if self.df.empty:
            return pd.DataFrame()

        latest_data = (
            self.df.sort_values('load_timestamp_utc')
            .groupby('city')
            .last()
            .reset_index()
        )
        # Reorder cities
        latest_data['city'] = pd.Categorical(
            latest_data['city'],
            categories=self.cities_order,
            ordered=True
        )
        return latest_data.sort_values('city')
    
    def convert_df_to_csv(self, df):
        """Convert DataFrame to CSV for download"""
        return df.to_csv(index=False).encode('utf-8')

    def display_header(self):
        """Display the main header"""
        st.markdown('<h1 class="main-header">Weather Dashboard</h1>', unsafe_allow_html=True)

        if self.df.empty:
            st.warning("No weather data available. Please run the data pipeline first.")
            return False
        return True

    def display_city_card(self, city_data):
        """Detailed city card"""
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            st.markdown(f"""
            <div class="city-card">
                <h3 style="margin: 0; color: #2c3e50;">{city_data['city']}</h3>
                <p class="weather-description" style="margin: 0.5rem 0;">{city_data['weather_description'].title()}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='text-align: center; padding: 1rem;'>
                <div class="temperature-value">{city_data['temperature_celsius']:.1f}°C</div>
                <div style='font-size: 0.8rem; color: #7f8c8d;'>Feels like {city_data['feels_like_celsius']:.1f}°C</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='padding: 1rem;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                    <span style='font-size: 0.9rem;'>💧 Humidity</span>
                    <span style='font-weight: bold;'>{city_data['humidity_percent']}%</span>
                </div>
                <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                    <span style='font-size: 0.9rem;'>💨 Wind</span>
                    <span style='font-weight: bold;'>{city_data['wind_speed_mps']} m/s</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='font-size: 0.9rem;'>📍 Coordinates</span>
                    <span style='font-size: 0.8rem; color: #7f8c8d;'>
                        {city_data['latitude']:.2f}, {city_data['longitude']:.2f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def display_temperature_chart(self, latest_data):
        """Bar chart of temperatures"""
        st.markdown('<div class="section-header">Temperature Overview</div>', unsafe_allow_html=True)

        if latest_data.empty:
            return

        fig = px.bar(
            latest_data,
            x='city',
            y='temperature_celsius',
            color='temperature_celsius',
            hover_data=['humidity_percent', 'wind_speed_mps', 'feels_like_celsius'],
            color_continuous_scale='Blues',
            height=300
        )

        fig.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title=None,
            yaxis_title="Temperature (°C)",
            yaxis_range=[
                min(20, latest_data['temperature_celsius'].min() - 2),
                max(35, latest_data['temperature_celsius'].max() + 2)
            ]
        )

        st.plotly_chart(fig, use_container_width=True)

    def display_metrics(self, latest_data):
        """Key metrics row"""
        if latest_data.empty:
            return

        col1, col2, col3, col4 = st.columns(4)

        metrics = [
            ("🌡️ Avg Temp", f"{latest_data['temperature_celsius'].mean():.1f}°C"),
            ("💧 Avg Humidity", f"{latest_data['humidity_percent'].mean():.0f}%"),
            ("💨 Avg Wind", f"{latest_data['wind_speed_mps'].mean():.1f} m/s"),
            ("🏙️ Cities", str(len(latest_data)))
        ]

        for col, (label, value) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style='font-size: 0.9rem; color: #7f8c8d;'>{label}</div>
                    <div style='font-size: 1.5rem; font-weight: bold; color: #2c3e50;'>{value}</div>
                </div>
                """, unsafe_allow_html=True)

    def display_city_card_simple(self, city_data):
        """Simplified city card"""
        st.markdown(f"""
        <div class="city-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="margin: 0; color: #2c3e50;">{city_data['city']}</h4>
                <div class="temperature-value" style="font-size: 1.2rem;">{city_data['temperature_celsius']:.1f}°C</div>
            </div>
            <p class="weather-description" style="margin: 0.3rem 0;">{city_data['weather_description'].title()}</p>
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #7f8c8d;">
                <span>💧 {city_data['humidity_percent']}%</span>
                <span>💨 {city_data['wind_speed_mps']} m/s</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_dataset_section(self):
        """Display dataset and download options"""
        st.markdown("---")
        st.markdown('<div class="section-header">Weather Dataset</div>', unsafe_allow_html=True)
        
        # Show dataset info
        st.markdown(f"""
        <div style="margin-bottom: 1rem; font-size: 0.9rem; color: #7f8c8d;">
            Dataset contains {len(self.df)} records from {self.df['timestamp_utc'].min().strftime('%Y-%m-%d')} to {self.df['timestamp_utc'].max().strftime('%Y-%m-%d')}
        </div>
        """, unsafe_allow_html=True)
        
        # Display the dataset with a subset of columns for better readability
        display_cols = ['city', 'temperature_celsius', 'feels_like_celsius', 
                       'humidity_percent', 'wind_speed_mps', 'weather_description', 
                       'timestamp_utc']
        
        st.dataframe(
            self.df[display_cols].sort_values('timestamp_utc', ascending=False),
            use_container_width=True,
            height=300
        )
        
        # Download button
        st.download_button(
            label="Download Full Dataset as CSV",
            data=self.convert_df_to_csv(self.df),
            file_name=f"weather_data_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="full-download"
        )

    def run(self):
        """Run the dashboard"""
        if not self.display_header():
            return

        latest_data = self.get_latest_data()  # ✅ compute once

        # Metrics
        self.display_metrics(latest_data)
        st.markdown("---")

        # Temperature chart
        self.display_temperature_chart(latest_data)
        st.markdown("---")

        # City grid
        st.markdown('<div class="section-header">All Cities</div>', unsafe_allow_html=True)
        if not latest_data.empty:
            cols = st.columns(min(len(latest_data), 3))
            for idx, (_, row) in enumerate(latest_data.iterrows()):
                with cols[idx % 3]:
                    self.display_city_card_simple(row)
        
        # Dataset section
        self.display_dataset_section()

        # Last update
        if not self.df.empty:
            latest_update = self.df['load_timestamp_utc'].max()
            st.caption(f"Last updated: {latest_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")


# Run app
if __name__ == "__main__":
    dashboard = WeatherDashboard()
    dashboard.run()