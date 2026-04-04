import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import HomeScreen from './src/screens/HomeScreen';
import LocationSafetyScreen from './src/screens/LocationSafetyScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator 
        initialRouteName="HomeScreen"
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen 
          name="HomeScreen" 
          component={HomeScreen} 
        />
        <Stack.Screen 
          name="LocationSafetyScreen" 
          component={LocationSafetyScreen} 
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
