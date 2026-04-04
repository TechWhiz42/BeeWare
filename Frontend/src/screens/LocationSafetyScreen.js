import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  ActivityIndicator, 
  Alert,
  Keyboard,
  Dimensions,
  Platform,
  Image,
  StatusBar
} from 'react-native';
import MapView, { Marker, Circle } from 'react-native-maps';
import * as Location from 'expo-location';
import Ionicons from '@expo/vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { API_BASE_URL } from '../config';

const { width } = Dimensions.get('window');

const UI_COLORS = {
  background: '#F8F9FA',
  card: 'rgba(255, 255, 255, 0.95)',
  text: '#111111',
  textMuted: '#666666',
  safety: '#E5A015', // matching logo's golden yellow
  crime: '#E63946',
  survivability: '#8338EC',
  divider: '#E0E0E0'
};

const METER_IMAGES = {
  safety: {
    green: require('../../assets/meter/Green.png'),
    yellow: require('../../assets/meter/Yellow.png'),
    orange: require('../../assets/meter/Orange.png'),
    red: require('../../assets/meter/Red.png'),
  },
  crime: {
    part: require('../../assets/meter/Cr_part.png'),
    half: require('../../assets/meter/Cr_half.png'),
    full: require('../../assets/meter/Cr_full.png'),
  },
  survivability: {
    part: require('../../assets/meter/Sur_part.png'),
    half: require('../../assets/meter/Sur_half.png'),
    full: require('../../assets/meter/Sur_full.png'),
  }
};

const getMeterImage = (mode, score) => {
  if (mode === 'safety') {
    if (score >= 70) return METER_IMAGES.safety.green;
    if (score >= 40) return METER_IMAGES.safety.yellow;
    return METER_IMAGES.safety.red; // Assuming red/orange mapped to high risk. Let's return red for the lowest to match a 3-step system.
  } else if (mode === 'crime') {
    if (score <= 30) return METER_IMAGES.crime.part;   // Low Crime
    if (score <= 60) return METER_IMAGES.crime.half;   // Moderate Crime
    return METER_IMAGES.crime.full;                    // High Crime
  } else if (mode === 'survivability') {
    if (score >= 70) return METER_IMAGES.survivability.full; // High Survivability
    if (score >= 40) return METER_IMAGES.survivability.half; // Moderate Survivability
    return METER_IMAGES.survivability.part;                  // Low Survivability
  }
};

const getSuggestions = (mode, score) => {
  let label = "Moderate Risk";
  let suggestions = [];

  if (mode === 'safety') {
    if (score >= 70) {
      label = "Safe";
      suggestions = ["Generally safe to walk", "Standard precautions apply"];
    } else if (score >= 40) {
      label = "Moderate Risk";
      suggestions = ["Avoid isolated streets", "Prefer well-lit areas", "Stay alert around corners"];
    } else {
      label = "High Risk";
      suggestions = ["Avoid walking alone", "Use trusted transportation", "Stick to crowded main streets"];
    }
  } else if (mode === 'crime') {
    if (score <= 30) {
      label = "Low Crime";
      suggestions = ["Low incidents reported", "Normal awareness needed"];
    } else if (score <= 60) {
      label = "Moderate Crime";
      suggestions = ["Watch for belongings", "Avoid dark alleyways", "Keep bags zipped"];
    } else {
      label = "High Crime";
      suggestions = ["Keep valuables hidden", "Remain highly vigilant", "Do not linger at night"];
    }
  } else if (mode === 'survivability') {
    if (score >= 70) {
      label = "High Survivability";
      suggestions = ["Quick emergency access", "Multiple hospitals nearby"];
    } else if (score >= 40) {
      label = "Moderate Access";
      suggestions = ["Average emergency response", "Know your exact location"];
    } else {
      label = "Low Access";
      suggestions = ["Limited fast response", "Travel with companions", "Carry basic first aid"];
    }
  }

  return { label, suggestions };
};

const getModeColor = (mode) => {
  switch (mode) {
    case 'safety': return UI_COLORS.safety;
    case 'crime': return UI_COLORS.crime;
    case 'survivability': return UI_COLORS.survivability;
    default: return UI_COLORS.safety;
  }
};

const LocationSafetyScreen = () => {
  const mapRef = useRef(null);
  const [location, setLocation] = useState(null);
  const [mapRegion, setMapRegion] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [mode, setMode] = useState('safety'); 
  const [loading, setLoading] = useState(false);
  const [rawData, setRawData] = useState(null);

  const [timestamp, setTimestamp] = useState(new Date());
  const [showTimePicker, setShowTimePicker] = useState(false);

  const [cardExpanded, setCardExpanded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        let { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          return;
        }

        let currentLocation = await Location.getCurrentPositionAsync({});
        const coords = {
          latitude: currentLocation.coords.latitude,
          longitude: currentLocation.coords.longitude,
        };
        setLocation(coords);
        
        const region = {
          ...coords,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        };
        setMapRegion(region);
        
        fetchSafetyData(coords.latitude, coords.longitude, timestamp);
      } catch (error) {
        console.log("Error getting location: ", error);
      }
    })();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    Keyboard.dismiss();
    setLoading(true);
    try {
      const geocoded = await Location.geocodeAsync(searchQuery);
      if (geocoded.length > 0) {
        const { latitude, longitude } = geocoded[0];
        const coords = { latitude, longitude };
        setLocation(coords);
        
        const region = { ...coords, latitudeDelta: 0.05, longitudeDelta: 0.05 };
        setMapRegion(region);
        if (mapRef.current) {
          mapRef.current.animateToRegion(region, 1000);
        }
        
        fetchSafetyData(latitude, longitude, timestamp);
      } else {
        Alert.alert('Not Found', 'Could not find the specified location.');
        setLoading(false);
      }
    } catch (error) {
      console.log(error);
      setLoading(false);
    }
  };

  const handleMapPress = (e) => {
    const coords = e.nativeEvent.coordinate;
    setLocation(coords);
    fetchSafetyData(coords.latitude, coords.longitude, timestamp);
  };

  const fetchSafetyData = async (lat, lng, timeToUse) => {
    setLoading(true);
    setRawData(null);
    try {
      const response = await fetch(`${API_BASE_URL}/location/safety`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: lat,
          longitude: lng,
          timestamp: timeToUse.toISOString()
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      const data = await response.json();
      setRawData(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const onTimeChange = (event, selectedTime) => {
    setShowTimePicker(Platform.OS === 'ios');
    if (selectedTime) {
      const currentDate = new Date(timestamp);
      currentDate.setHours(selectedTime.getHours(), selectedTime.getMinutes());
      setTimestamp(currentDate);
      
      if (location) {
        fetchSafetyData(location.latitude, location.longitude, currentDate);
      }
    }
  };

  let currentScore = 0;
  if (rawData) {
    if (mode === 'safety') {
      currentScore = rawData.safety_score || 0;
    } else if (mode === 'crime') {
      let impact = rawData.crime_impact_score || 0;
      currentScore = impact > 10 ? impact : (impact * 10);
    } else if (mode === 'survivability') {
      currentScore = rawData.survivability_score || 0;
    }
  }
  currentScore = Math.round(currentScore);

  const { label, suggestions } = getSuggestions(mode, currentScore);
  const themeColor = getModeColor(mode);

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        region={mapRegion}
        showsUserLocation={true}
        onPress={handleMapPress}
        zoomEnabled={false}
      >
        {location && (
          <>
            <Marker coordinate={location}>
              <View style={[styles.markerDot, { backgroundColor: themeColor }]} />
            </Marker>
            <Circle
              center={location}
              radius={800} 
              fillColor={`${themeColor}33`}
              strokeColor={themeColor}
              strokeWidth={1.5}
            />
          </>
        )}
      </MapView>

      <View style={styles.topSection} pointerEvents="box-none">
        <View style={styles.topControls}>
          <View style={styles.searchInputContainer}>
            <Ionicons name="search" size={16} color={UI_COLORS.textMuted} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search area..."
              placeholderTextColor={UI_COLORS.textMuted}
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
          </View>
          <TouchableOpacity 
            style={styles.timeBtn} 
            onPress={() => setShowTimePicker(true)}
          >
            <Ionicons name="time" size={18} color={UI_COLORS.text} />
            <Text style={styles.timeText}>
              {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.modeContainer}>
          {['safety', 'crime', 'survivability'].map((m) => {
            const isActive = mode === m;
            return (
              <TouchableOpacity
                key={m}
                style={[
                  styles.modePill,
                  isActive && styles.modePillActive
                ]}
                onPress={() => setMode(m)}
              >
                <Text style={[
                  styles.modeText,
                  isActive && styles.modeTextActive
                ]}>
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {showTimePicker && (
        <DateTimePicker
          value={timestamp}
          mode="time"
          display="spinner"
          themeVariant="light"
          textColor="#000000"
          onChange={onTimeChange}
        />
      )}

      <View style={styles.bottomSection}>
        {loading ? (
          <View style={styles.card}>
            <ActivityIndicator size="large" color={UI_COLORS.safety} />
          </View>
        ) : rawData ? (
          <TouchableOpacity 
            activeOpacity={0.95} 
            onPress={() => setCardExpanded(!cardExpanded)}
            style={styles.card}
          >
            <View style={styles.cardHandle} />
            
            <View style={styles.scoreRow}>
              <Image source={getMeterImage(mode, currentScore)} style={styles.meterImage} resizeMode="contain" />
              <View style={styles.scoreTextContainer}>
                <Text style={[styles.scoreValue, { color: themeColor }]}>
                  <Text style={styles.scorePrefix}>Score: </Text>
                  {currentScore}
                </Text>
                <Text style={styles.scoreLabel}>{label}</Text>
              </View>
            </View>

            {cardExpanded && (
              <View style={styles.expandedContent}>
                <View style={styles.divider} />

                <View style={styles.suggestionsContainer}>
                  {suggestions.map((s, idx) => (
                    <View key={idx} style={styles.suggestionItem}>
                      <Ionicons name="shield-checkmark" size={16} color={themeColor} style={styles.suggestionIcon} />
                      <Text style={styles.suggestionText}>{s}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            <Text style={styles.expandText}>
              {cardExpanded ? "View Less" : "View More"}
            </Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.card}>
            <Text style={styles.instructionText}>Tap or search a place for analysis</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: UI_COLORS.background,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  markerDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: '#E5E5E5',
  },
  topSection: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 55 : (StatusBar.currentHeight || 24) + 15,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
  },
  topControls: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: UI_COLORS.card,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  searchInput: {
    flex: 1,
    color: UI_COLORS.text,
    fontSize: 14,
    marginLeft: 6,
  },
  timeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: UI_COLORS.card,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginLeft: 8,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  timeText: {
    color: UI_COLORS.text,
    fontSize: 13, // Smaller text
    fontWeight: '600',
    marginLeft: 4,
  },
  modeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  modePill: {
    backgroundColor: UI_COLORS.card,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  modePillActive: {
    backgroundColor: UI_COLORS.safety,
  },
  modeText: {
    color: UI_COLORS.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  modeTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  bottomSection: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 25 : 15,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  card: {
    backgroundColor: UI_COLORS.card,
    borderRadius: 18,
    padding: 18,
    marginHorizontal: 0,
    width: '100%',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  cardHandle: {
    width: 35,
    height: 4,
    backgroundColor: UI_COLORS.divider,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 14,
  },
  scoreRow: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  meterImage: {
    width: 42,
    height: 42,
    marginLeft: 16,
  },
  scoreTextContainer: {
    justifyContent: 'center',
  },
  scoreValue: {
    fontSize: 42,
    fontWeight: '800',
  },
  scorePrefix: {
    fontSize: 24,
    color: UI_COLORS.text,
    fontWeight: '600',
  },
  expandedContent: {
    marginTop: 6,
  },
  scoreLabel: {
    fontSize: 18,
    color: UI_COLORS.text,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  divider: {
    height: 1,
    backgroundColor: UI_COLORS.divider,
    marginVertical: 12,
  },
  suggestionsContainer: {
    gap: 10,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  suggestionIcon: {
    marginRight: 10,
    marginTop: 2,
  },
  suggestionText: {
    color: UI_COLORS.text,
    fontSize: 14,
    flex: 1,
    lineHeight: 20,
    fontWeight: '500',
  },
  expandText: {
    color: UI_COLORS.textMuted,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 14,
    fontWeight: '600',
  },
  instructionText: {
    color: UI_COLORS.textMuted,
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '500',
    marginVertical: 8,
  }
});

export default LocationSafetyScreen;
