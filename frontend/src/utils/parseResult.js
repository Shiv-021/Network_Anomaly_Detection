/**
 * Normalise raw Flask API responses into a consistent shape for rendering.
 */
export function parseResult(rawData, endpoint) {
  let pred = rawData.predictions?.[0] ?? rawData

  if (endpoint === '/predict') {
    return {
      isAnomaly:   pred.is_anomaly,
      mainLabel:   pred.is_anomaly ? 'ANOMALY' : 'NORMAL',
      mainScore:   pred.anomaly_probability ?? 0,
      endpoint,
      attackClass:       null,
      attackConfidence:  null,
      topPredictions:    null,
      binary:        { isAnomaly: pred.is_anomaly, anomalyProb: pred.anomaly_probability, threshold: pred.threshold_used },
      multiclass:    null,
      reconstruction: null,
    }
  }

  if (endpoint === '/predict/attack-type') {
    const isNormal = pred.predicted_class?.toLowerCase() === 'normal'
    // Extract top 5 predictions from class_probabilities
    const topPredictions = pred.class_probabilities
      ? Object.entries(pred.class_probabilities)
          .map(([cls, prob]) => ({ class: cls, probability: prob }))
          .sort((a, b) => b.probability - a.probability)
          .slice(0, 5)
      : null
    return {
      isAnomaly:   !isNormal,
      mainLabel:   isNormal ? 'NORMAL' : 'ANOMALY',
      mainScore:   isNormal ? (1 - pred.confidence) : pred.confidence,
      endpoint,
      attackClass:      pred.predicted_class,
      attackConfidence: pred.confidence,
      topPredictions,
      binary:        null,
      multiclass:    { class: pred.predicted_class, confidence: pred.confidence },
      reconstruction: null,
    }
  }

  if (endpoint === '/predict/reconstruction') {
    const thr = pred.threshold_used || 0.05
    const score = Math.min(pred.reconstruction_error / (thr * 2), 1)
    return {
      isAnomaly:   pred.is_anomaly,
      mainLabel:   pred.is_anomaly ? 'ANOMALY' : 'NORMAL',
      mainScore:   score,
      endpoint,
      attackClass:      null,
      attackConfidence: null,
      topPredictions:   null,
      binary:        null,
      multiclass:    null,
      reconstruction: { error: pred.reconstruction_error, isAnomaly: pred.is_anomaly, threshold: pred.threshold_used },
    }
  }

  if (endpoint === '/predict/full') {
    const bin = pred.binary || {}
    const atk = pred.attack_type || {}
    const rec = pred.reconstruction || {}
    const isNormal = atk.predicted_class?.toLowerCase() === 'normal'
    const attackClass = atk.predicted_class || null
    const binaryIsAnomaly = bin.is_anomaly ?? !isNormal
    // The binary model and the multiclass model are independently trained
    // and can disagree: binary says "not anomalous" (below its 0.5
    // threshold) while multiclass confidently names a specific attack
    // (e.g. a borderline "teardrop" sample scoring ~26% on the binary
    // model but ~98% confidence on the multiclass one). Surface that
    // disagreement explicitly instead of only showing the binary verdict's
    // clean NORMAL badge next to a contradicting attack-class name.
    const mixedSignal = !binaryIsAnomaly && attackClass != null
      && !['normal', 'other_rare'].includes(attackClass.toLowerCase())
    return {
      isAnomaly:   binaryIsAnomaly,
      mainLabel:   binaryIsAnomaly ? 'ANOMALY' : 'NORMAL',
      mainScore:   bin.anomaly_probability ?? 0,
      endpoint,
      attackClass,
      attackConfidence: atk.confidence || null,
      topPredictions:   null,
      mixedSignal,
      binary:        bin.is_anomaly !== undefined
                       ? { isAnomaly: bin.is_anomaly, anomalyProb: bin.anomaly_probability }
                       : null,
      multiclass:    attackClass
                       ? { class: attackClass, confidence: atk.confidence }
                       : null,
      reconstruction: rec.reconstruction_error !== undefined
                        ? { error: rec.reconstruction_error, isAnomaly: rec.is_anomaly }
                        : null,
    }
  }

  return null
}
