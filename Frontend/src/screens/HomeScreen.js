import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';

const UI_COLORS = {
  background: '#0D0D0D',
  card: '#1A1A1A',
  text: '#FFFFFF',
  textMuted: '#A0A0A0',
  safety: '#E5A015',
};

const HomeScreen = ({ navigation }) => {
  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <Image 
          source={require('../../assets/images/Full.png')} 
          style={styles.logoImage} 
          resizeMode="contain" 
        />
      </View>
      <Text style={styles.subtitle}>Your companion for safe navigation</Text>
      
      <TouchableOpacity 
        style={styles.button}
        onPress={() => navigation.navigate('LocationSafetyScreen')}
        activeOpacity={0.8}
      >
        <Text style={styles.buttonText}>Start Safety Analysis</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: UI_COLORS.background,
    padding: 30,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  logoImage: {
    width: 280,
    height: 80,
  },
  subtitle: {
    fontSize: 16,
    color: UI_COLORS.textMuted,
    marginBottom: 60,
    textAlign: 'center',
  },
  button: {
    backgroundColor: UI_COLORS.safety,
    paddingVertical: 18,
    paddingHorizontal: 40,
    borderRadius: 30,
    elevation: 5,
    shadowColor: UI_COLORS.safety,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  buttonText: {
    color: '#0D0D0D',
    fontSize: 18,
    fontWeight: '800',
  },
});

export default HomeScreen;
