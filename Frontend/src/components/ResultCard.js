import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const ResultCard = ({ data }) => {
  if (!data) return null;

  return (
    <View style={[styles.card, { borderTopColor: data.color }]}>
      <Text style={[styles.label, { color: data.color }]}>{data.label}</Text>
      
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Safety Score:</Text>
        <Text style={styles.metricValue}>{data.safety_score.toFixed(2)}</Text>
      </View>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Survivability Score:</Text>
        <Text style={styles.metricValue}>{data.survivability_score.toFixed(2)}</Text>
      </View>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Crime Impact Score:</Text>
        <Text style={styles.metricValue}>{data.crime_impact_score.toFixed(2)}</Text>
      </View>
      
      <View style={styles.divider} />
      
      <Text style={styles.sectionTitle}>Probabilities</Text>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Safe:</Text>
        <Text style={styles.metricValue}>{(data.probability_safe * 100).toFixed(1)}%</Text>
      </View>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Caution:</Text>
        <Text style={styles.metricValue}>{(data.probability_caution * 100).toFixed(1)}%</Text>
      </View>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>High Risk:</Text>
        <Text style={styles.metricValue}>{(data.probability_high_risk * 100).toFixed(1)}%</Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Crime Density:</Text>
        <Text style={styles.metricValue}>{data.crime_density.toFixed(2)}</Text>
      </View>
      <View style={styles.metricContainer}>
        <Text style={styles.metricLabel}>Confidence:</Text>
        <Text style={styles.metricValue}>{(data.confidence * 100).toFixed(1)}%</Text>
      </View>

      <View style={styles.divider} />

      <Text style={styles.sectionTitle}>Explanation</Text>
      {data.explanation.map((item, index) => (
        <Text key={index} style={styles.explanationText}>• {item}</Text>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginVertical: 10,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    borderTopWidth: 6,
  },
  label: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  metricContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 16,
    color: '#555',
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  divider: {
    height: 1,
    backgroundColor: '#eee',
    marginVertical: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#444',
  },
  explanationText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
    lineHeight: 20,
  },
});

export default ResultCard;
