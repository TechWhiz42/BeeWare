import { StyleSheet, View, TextInput, Text, Image } from 'react-native';
import MapView, { Circle, Polyline, Region } from 'react-native-maps';
import { useState } from 'react';
import * as Location from 'expo-location';

export default function App() {

  const [screen, setScreen] = useState<'home' | 'point' | 'route'>('home');
  const [mode, setMode] = useState<'safety' | 'crime' | 'survivability'>('safety');

  const [region, setRegion] = useState<Region>({
    latitude: 26.8319,
    longitude: 80.9163,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });

  const [search, setSearch] = useState("Charbagh");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  const [score, setScore] = useState(50);
  const [showInfo, setShowInfo] = useState(false);
  const [routeCoords, setRouteCoords] = useState<any[]>([]);

  // 🎨 COLORS
  const getColor = () => {
    if (mode === 'crime') return 'rgba(180,0,0,0.25)';
    if (mode === 'survivability') return 'rgba(138,43,226,0.25)';
    return 'rgba(0,0,0,0.2)';
  };

  // 🖼️ METERS
  const getMeter = () => {

    if (mode === 'safety') {
      if (score < 25) return require('../../assets/meter/Red.png');
      if (score < 50) return require('../../assets/meter/Orange.png');
      if (score < 75) return require('../../assets/meter/Yellow.png');
      return require('../../assets/meter/Green.png');
    }

    if (mode === 'survivability') {
      if (score < 25) return require('../../assets/meter/Sur_emp.png');
      if (score < 50) return require('../../assets/meter/Sur_part.png');
      if (score < 75) return require('../../assets/meter/Sur_half.png');
      return require('../../assets/meter/Sur_full.png');
    }

    const crime = 100 - score;
    if (crime < 25) return require('../../assets/meter/Cr_emp.png');
    if (crime < 50) return require('../../assets/meter/Cr_part.png');
    if (crime < 75) return require('../../assets/meter/Cr_half.png');
    return require('../../assets/meter/Cr_full.png');
  };

  // 📍 SEARCH
  const handleSearch = async () => {
    const res = await Location.geocodeAsync(`${search}, Lucknow`);
    if (res.length > 0) {
      const { latitude, longitude } = res[0];
      setRegion({ latitude, longitude, latitudeDelta: 0.02, longitudeDelta: 0.02 });
    }
  };

  // 🛣️ ROUTE
  const handleRoute = async () => {
    const s = await Location.geocodeAsync(`${start}, Lucknow`);
    const e = await Location.geocodeAsync(`${end}, Lucknow`);

    if (!s.length || !e.length) return;

    setRouteCoords([
      { latitude: s[0].latitude, longitude: s[0].longitude },
      { latitude: e[0].latitude, longitude: e[0].longitude }
    ]);
  };

  return (
    <View style={{ flex: 1 }}>

      {/* 🏠 HOME */}
      {screen === 'home' && (
        <View style={styles.center}>
          <Image source={require('../../assets/images/logo.png')} style={styles.logo} />
          <Text style={styles.title}>BeeWare</Text>
          <Text style={styles.subtitle}>Stay aware. Stay safe.</Text>
          <Text style={styles.brand}>CODEBLOODED</Text>

          <Text style={styles.btn} onPress={() => setScreen('point')}>
            📍 Point Safety
          </Text>

          <Text style={styles.btn} onPress={() => setScreen('route')}>
            🛣️ Path Safety
          </Text>
        </View>
      )}

      {/* 📍 POINT */}
      {screen === 'point' && (
        <>
          <TextInput
            value={search}
            onChangeText={setSearch}
            onSubmitEditing={handleSearch}
            style={styles.search}
          />

          <View style={styles.tabs}>
            <Text onPress={() => setMode('safety')}>Safety</Text>
            <Text onPress={() => setMode('crime')}>Crime</Text>
            <Text onPress={() => setMode('survivability')}>Survivability</Text>
          </View>

          <MapView style={{ flex: 1 }} region={region}>
            <Circle center={region} radius={800} fillColor={getColor()} />
          </MapView>

          <View style={styles.meter}>
            {!showInfo ? (
              <Image source={getMeter()} style={{ width: 120, height: 60 }} />
            ) : (
              <Text>Stay alert. Avoid unsafe areas.</Text>
            )}

            <Text>Score: {score}</Text>

            <Text onPress={() => setShowInfo(!showInfo)}>
              {showInfo ? "🔙" : "ℹ️"}
            </Text>

            <Text onPress={() => setScreen('home')}>Back</Text>
          </View>
        </>
      )}

      {/* 🛣️ ROUTE */}
      {screen === 'route' && (
        <>
          <View style={styles.routeInput}>
            <TextInput placeholder="Start" value={start} onChangeText={setStart} />
            <TextInput placeholder="End" value={end} onChangeText={setEnd} />

            <Text style={styles.btn} onPress={handleRoute}>
              Check Route
            </Text>
          </View>

          <View style={styles.tabs}>
            <Text onPress={() => setMode('safety')}>Safety</Text>
            <Text onPress={() => setMode('crime')}>Crime</Text>
            <Text onPress={() => setMode('survivability')}>Survivability</Text>
          </View>

          <MapView style={{ flex: 1 }} region={region}>
            {routeCoords.length > 0 && (
              <Polyline coordinates={routeCoords} strokeWidth={4} strokeColor="black" />
            )}
          </MapView>

          <View style={styles.meter}>
            <Image source={getMeter()} style={{ width: 120, height: 60 }} />
            <Text>Score: {score}</Text>
            <Text onPress={() => setScreen('home')}>Back</Text>
          </View>
        </>
      )}

    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  logo: { width: 80, height: 80 },
  title: { fontSize: 28, fontWeight: 'bold' },
  subtitle: { color: '#666' },
  brand: { marginBottom: 30 },

  btn: {
    backgroundColor: '#FFD54F',
    padding: 12,
    marginTop: 10,
    borderRadius: 10,
  },

  search: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    backgroundColor: '#fff',
    padding: 10,
    zIndex: 2,
  },

  tabs: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
    zIndex: 2,
  },

  meter: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: '#fff',
    padding: 15,
    alignItems: 'center',
  },

  routeInput: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    zIndex: 2,
  },
});