import { useEffect, useState, useRef } from 'react';
import mqtt from 'mqtt';

export interface TelemetryData {
  battery: number;
  cpu: number;
  memory: number;
  speed: number;
  health: string;
  lat: number;
  lng: number;
}

export function useMqttTelemetry(initialState: TelemetryData) {
  const [telemetry, setTelemetry] = useState<TelemetryData>(initialState);
  const clientRef = useRef<mqtt.MqttClient | null>(null);

  useEffect(() => {
    // Connect to the public test Mosquitto broker via WebSockets
    const client = mqtt.connect('wss://test.mosquitto.org:8081/mqtt', {
      clientId: `dashboard_${Math.random().toString(16).slice(3)}`,
      clean: true,
      connectTimeout: 4000,
      reconnectPeriod: 1000,
    });
    clientRef.current = client;

    client.on('connect', () => {
      console.log('Connected to MQTT Broker via WebSockets');
      client.subscribe('telemetry/agro_ai_robot_001', (err) => {
        if (!err) {
          console.log('Subscribed to telemetry/agro_ai_robot_001');
        } else {
          console.error('Subscription error:', err);
        }
      });
    });

    client.on('message', (topic, message) => {
      if (topic === 'telemetry/agro_ai_robot_001') {
        try {
          const data = JSON.parse(message.toString());
          // Merge incoming data with existing telemetry state
          setTelemetry((prev) => {
            const newState = { ...prev };
            
            if (data.battery_level !== undefined) {
              newState.battery = data.battery_level;
            }
            if (data.health !== undefined) {
              newState.health = data.health;
            }
            
            // For now, we simulate CPU/memory updates locally if the backend doesn't send them
            newState.cpu = Math.floor(30 + Math.random() * 40);
            newState.memory = Math.floor(50 + Math.random() * 30);
            
            // if E-STOP is active, speed is 0
            newState.speed = newState.health === "E-STOP" ? 0.0 : +(Math.random() * 5).toFixed(1);
            
            return newState;
          });
        } catch (e) {
          console.error('Error parsing MQTT message:', e);
        }
      }
    });

    client.on('error', (err) => {
      console.error('MQTT Connection error: ', err);
      client.end();
    });

    return () => {
      console.log('Disconnecting from MQTT Broker');
      client.end();
      clientRef.current = null;
    };
  }, []);

  const triggerEStop = () => {
    if (clientRef.current) {
      clientRef.current.publish('command/agro_ai_robot_001', JSON.stringify({ command: 'E-STOP' }));
      console.log('Published E-STOP command to MQTT Broker');
    }
    // Optimistic UI update
    setTelemetry((prev) => ({ ...prev, health: 'E-STOP', speed: 0.0 }));
  };

  return { telemetry, setTelemetry, triggerEStop };
}
