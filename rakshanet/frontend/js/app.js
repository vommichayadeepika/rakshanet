// RakshaNet AI Disaster Response Coordination Platform
// Phase 5: Embedded React 18 + Leaflet Command Center Dashboard

const { useState, useEffect, useRef, useMemo, useCallback } = React;

// API Base URL (detects current origin or defaults to local FastAPI)
const API_BASE = window.location.origin.includes('http') ? window.location.origin : 'http://127.0.0.1:8000';

// Color Mapping Utility
const RISK_COLORS = {
  RED: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500', hex: '#ef4444', badge: 'bg-red-600' },
  ORANGE: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500', hex: '#f97316', badge: 'bg-orange-600' },
  YELLOW: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500', hex: '#eab308', badge: 'bg-yellow-600' },
  GREEN: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500', hex: '#22c55e', badge: 'bg-emerald-600' }
};

const URGENCY_COLORS = {
  critical: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500', hex: '#ef4444', badge: 'bg-red-600' },
  high: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500', hex: '#f97316', badge: 'bg-orange-600' },
  medium: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500', hex: '#eab308', badge: 'bg-amber-600' },
  low: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500', hex: '#3b82f6', badge: 'bg-blue-600' }
};

const LANGUAGE_LABELS = {
  te: 'Telugu',
  hi: 'Hindi',
  en: 'English',
  ta: 'Tamil',
  kn: 'Kannada',
  ml: 'Malayalam'
};

// Krishna River Delta Sector Coordinates Reference (Fallback & Validation)
const ZONE_COORDINATES = {
  1: [16.5091, 80.6034],
  2: [16.5230, 80.5980],
  3: [16.4980, 80.6280],
  4: [16.4950, 80.6650],
  5: [16.5280, 80.6720],
  6: [16.5160, 80.6550],
  7: [16.4800, 80.6020]
};

// =====================================================================
// MAIN COMMAND CENTER APPLICATION
// =====================================================================

function RakshaNetApp() {
  const [zones, setZones] = useState([]);
  const [intelligence, setIntelligence] = useState([]);
  const [sosReports, setSosReports] = useState([]);
  const [droneReadings, setDroneReadings] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [envReadings, setEnvReadings] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);

  // Filters & State
  const [activeTab, setActiveTab] = useState('zones'); // 'zones' | 'sos' | 'telemetry' | 'routes' | 'relief'
  const [sosLangFilter, setSosLangFilter] = useState('ALL');
  const [sosUrgencyFilter, setSosUrgencyFilter] = useState('ALL');
  const [layerVisibility, setLayerVisibility] = useState({
    zones: true,
    drones: true,
    sos: true,
    alerts: true,
    evacuation: true,        // Phase 7 – Recommended Evacuation route polylines
    alternativeRoutes: true, // Phase 7 – Alternative Evacuation route polylines
    droneRoutes: true,       // Phase 7 – Drone recon flight path polylines
    camps: true,             // Phase 8 – Relief Camps
    reliefTeams: true,       // Phase 8 – Relief Teams
    recovery: true,          // Phase 8 – Recovery Sites
  });

  // Phase 7 – Route Intelligence State
  const [evacuationRoutes, setEvacuationRoutes] = useState([]);
  const [droneReconMissions, setDroneReconMissions] = useState([]);
  const [routeLayersRef] = useState({ evacuation: [], altRoutes: [], droneRecon: [], shelters: [] });
  const [isRecalculatingRoutes, setIsRecalculatingRoutes] = useState(false);

  // Phase 8 – Post-Disaster Relief & Recovery State
  const [reliefSummary, setReliefSummary] = useState(null);
  const [reliefCamps, setReliefCamps] = useState([]);
  const [reliefRequests, setReliefRequests] = useState([]);
  const [reliefResources, setReliefResources] = useState([]);
  const [reliefTeams, setReliefTeams] = useState([]);
  const [recoveryItems, setRecoveryItems] = useState([]);
  const [damageAssessments, setDamageAssessments] = useState([]);
  const [reliefSubTab, setReliefSubTab] = useState('overview'); // 'overview'|'damage'|'camps'|'requests'|'resources'|'teams'|'recovery'
  const [reliefLayersRef] = useState({ camps: [], teams: [], recovery: [] });
  const [showNewRequestModal, setShowNewRequestModal] = useState(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [reliefFund, setReliefFund] = useState(null);
  const [reliefDonations, setReliefDonations] = useState([]);
  const [showDonateModal, setShowDonateModal] = useState(false);
  const [donationForm, setDonationForm] = useState({ donor_name: '', amount: 500, message: '' });
  const [isDonating, setIsDonating] = useState(false);
  const [donationSuccess, setDonationSuccess] = useState(null);
  const [selectedCommunityTeamId, setSelectedCommunityTeamId] = useState(null);
  const [communityMessageModal, setCommunityMessageModal] = useState({ open: false, request: null, text: '' });

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [isSimulatingEvent, setIsSimulatingEvent] = useState(false);
  const [statusMessage, setStatusMessage] = useState({ text: 'Connecting to RakshaNet Grid...', type: 'info' });

  // Offline Alert System State
  const [isOnline, setIsOnline] = useState(typeof window !== 'undefined' ? window.navigator.onLine : true);
  const [isSimulatedOffline, setIsSimulatedOffline] = useState(false);
  const [offlineCacheTimestamp, setOfflineCacheTimestamp] = useState(() => {
    try {
      const c = localStorage.getItem('rakshanet_offline_cache');
      return c ? (JSON.parse(c).timestamp || 'Previous Session') : null;
    } catch(e) { return null; }
  });

  const [showNLPModal, setShowNLPModal] = useState(false);

  // WebSocket Live Real-Time State
  const [wsStatus, setWsStatus] = useState('CONNECTING'); // 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING'
  const [liveBanner, setLiveBanner] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const mapRef = useRef(null);
  const leafletMapRef = useRef(null);
  const markersRef = useRef({ zones: [], drones: [], sos: [], circles: [] });

  // -------------------------------------------------------------------
  // DATA FETCHING (INITIAL & BACKUP)
  // -------------------------------------------------------------------
  const fetchAllData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [
        intelRes, sosRes, droneRes, alertRes, envRes, evacRes, reconRes,
        summaryRes, campsRes, reqsRes, resourcesRes, teamsRes, recoveryRes, damageRes,
        fundRes, donationsRes
      ] = await Promise.all([
        fetch(`${API_BASE}/zone-intelligence`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE}/sos?limit=50`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE}/drone-readings?limit=50`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE}/alerts?limit=20`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE}/environmental-readings`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE}/routes/evacuation`).then(r => r.ok ? r.json() : []),   // Phase 7
        fetch(`${API_BASE}/routes/drone-recon`).then(r => r.ok ? r.json() : []),   // Phase 7
        fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null),     // Phase 8
        fetch(`${API_BASE}/relief/camps`).then(r => r.ok ? r.json() : []),          // Phase 8
        fetch(`${API_BASE}/relief/requests`).then(r => r.ok ? r.json() : []),       // Phase 8
        fetch(`${API_BASE}/relief/resources`).then(r => r.ok ? r.json() : []),      // Phase 8
        fetch(`${API_BASE}/relief/teams`).then(r => r.ok ? r.json() : []),          // Phase 8
        fetch(`${API_BASE}/relief/recovery`).then(r => r.ok ? r.json() : []),       // Phase 8
        fetch(`${API_BASE}/relief/damage-assessments`).then(r => r.ok ? r.json() : []), // Phase 8
        fetch(`${API_BASE}/relief/funds`).then(r => r.ok ? r.json() : null),        // Phase 8 fundraising
        fetch(`${API_BASE}/relief/donations?limit=10`).then(r => r.ok ? r.json() : []) // Phase 8 fundraising
      ]);

      setIntelligence(Array.isArray(intelRes) ? intelRes : []);
      setSosReports(Array.isArray(sosRes) ? sosRes : []);
      setDroneReadings(Array.isArray(droneRes) ? droneRes : []);
      setAlerts(Array.isArray(alertRes) ? alertRes : []);
      setEnvReadings(Array.isArray(envRes) ? envRes : []);
      setEvacuationRoutes(Array.isArray(evacRes) ? evacRes : []);           // Phase 7
      setDroneReconMissions(Array.isArray(reconRes) ? reconRes : []);       // Phase 7

      if (summaryRes) setReliefSummary(summaryRes);                         // Phase 8
      setReliefCamps(Array.isArray(campsRes) ? campsRes : []);
      setReliefRequests(Array.isArray(reqsRes) ? reqsRes : []);
      setReliefResources(Array.isArray(resourcesRes) ? resourcesRes : []);
      setReliefTeams(Array.isArray(teamsRes) ? teamsRes : []);
      setRecoveryItems(Array.isArray(recoveryRes) ? recoveryRes : []);
      setDamageAssessments(Array.isArray(damageRes) ? damageRes : []);
      if (fundRes) setReliefFund(fundRes);
      setReliefDonations(Array.isArray(donationsRes) ? donationsRes : []);

      // Cache snapshot locally for Offline Mode
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setOfflineCacheTimestamp(nowStr);
      try {
        const cacheObj = {
          timestamp: nowStr,
          date: new Date().toLocaleDateString(),
          intelligence: Array.isArray(intelRes) ? intelRes : [],
          sosReports: Array.isArray(sosRes) ? sosRes : [],
          droneReadings: Array.isArray(droneRes) ? droneRes : [],
          alerts: Array.isArray(alertRes) ? alertRes : [],
          envReadings: Array.isArray(envRes) ? envRes : [],
          evacuationRoutes: Array.isArray(evacRes) ? evacRes : [],
          reliefSummary: summaryRes,
          reliefCamps: Array.isArray(campsRes) ? campsRes : [],
          reliefRequests: Array.isArray(reqsRes) ? reqsRes : [],
          reliefResources: Array.isArray(resourcesRes) ? resourcesRes : [],
          reliefTeams: Array.isArray(teamsRes) ? teamsRes : [],
          recoveryItems: Array.isArray(recoveryRes) ? recoveryRes : [],
          damageAssessments: Array.isArray(damageRes) ? damageRes : [],
          reliefFund: fundRes,
          reliefDonations: Array.isArray(donationsRes) ? donationsRes : []
        };
        localStorage.setItem('rakshanet_offline_cache', JSON.stringify(cacheObj));
      } catch (cacheErr) {
        console.warn('[RakshaNet Offline Cache] Notice:', cacheErr);
      }

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setStatusMessage({ text: 'Operating in Offline/Cached Mode', type: 'error' });

      // Fallback: Read local cache snapshot
      try {
        const rawCache = localStorage.getItem('rakshanet_offline_cache');
        if (rawCache) {
          const cacheObj = JSON.parse(rawCache);
          if (cacheObj.intelligence) setIntelligence(cacheObj.intelligence);
          if (cacheObj.alerts) setAlerts(cacheObj.alerts);
          if (cacheObj.sosReports) setSosReports(cacheObj.sosReports);
          if (cacheObj.droneReadings) setDroneReadings(cacheObj.droneReadings);
          if (cacheObj.envReadings) setEnvReadings(cacheObj.envReadings);
          if (cacheObj.evacuationRoutes) setEvacuationRoutes(cacheObj.evacuationRoutes);
          if (cacheObj.reliefSummary) setReliefSummary(cacheObj.reliefSummary);
          if (cacheObj.reliefCamps) setReliefCamps(cacheObj.reliefCamps);
          if (cacheObj.reliefRequests) setReliefRequests(cacheObj.reliefRequests);
          if (cacheObj.reliefTeams) setReliefTeams(cacheObj.reliefTeams);
          if (cacheObj.damageAssessments) setDamageAssessments(cacheObj.damageAssessments);
          if (cacheObj.reliefFund) setReliefFund(cacheObj.reliefFund);
          if (cacheObj.reliefDonations) setReliefDonations(cacheObj.reliefDonations);
          setOfflineCacheTimestamp(cacheObj.timestamp || 'Previous Session');
        }
      } catch(e) {}
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Online / Offline Browser Listener
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setLiveBanner({
        title: '🌐 CONNECTION RESTORED',
        text: 'Reconnected to RakshaNet Operations Grid. Live data stream resynced.',
        type: 'info'
      });
      fetchAllData();
    };
    const handleOffline = () => {
      setIsOnline(false);
      setLiveBanner({
        title: '⚡ OFFLINE MODE ACTIVATED',
        text: 'Internet connection lost. Displaying cached emergency snapshot.',
        type: 'warning'
      });
    };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [fetchAllData]);


  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // -------------------------------------------------------------------
  // WEBSOCKET CONNECTION & AUTO-RECONNECT ENGINE
  // -------------------------------------------------------------------
  const connectWebSocket = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:8000';
    const wsUrl = `${protocol}//${host}/ws`;

    console.log(`[RakshaNet] Connecting WebSocket: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      console.log('[RakshaNet] WebSocket connection established successfully.');
      setWsStatus('CONNECTED');
      reconnectAttemptsRef.current = 0;
      setStatusMessage({ text: 'Live WebSocket synchronized with backend', type: 'success' });
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('[RakshaNet WS Received]', msg.event, msg);

        if (msg.event === 'CONNECTED') {
          setWsStatus('CONNECTED');
        } else if (msg.event === 'NEW_SOS') {
          const newSos = msg.data;
          setSosReports(prev => {
            if (prev.some(s => s.id === newSos.id)) return prev;
            return [newSos, ...prev];
          });
          setLiveBanner({
            title: `🚨 Live Distress Signal (${(newSos.urgency || 'critical').toUpperCase()})`,
            text: `"${newSos.message}"`,
            type: 'sos'
          });
          setStatusMessage({ text: `New live SOS: "${newSos.message.slice(0, 35)}..."`, type: 'urgent' });
        } else if (msg.event === 'ZONE_INTELLIGENCE_UPDATED') {
          setIntelligence(msg.data);
          setLiveBanner({
            title: '🧠 AI Risk Engine Live Recalculation',
            text: 'Updated flood risk scores and operational action priorities.',
            type: 'risk'
          });
          // Synchronize evacuation routes with updated risk scores
          fetch(`${API_BASE}/routes/evacuation`).then(r => r.ok ? r.json() : []).then(data => {
            if (Array.isArray(data) && data.length > 0) setEvacuationRoutes(data);
          }).catch(()=>{});
        } else if (msg.event === 'NEW_DRONE_READING') {
          setDroneReadings(prev => [msg.data, ...prev]);
          setLiveBanner({
            title: '🚁 Drone Aerial Telemetry',
            text: msg.message || `Road ${msg.data.road_status}: ${msg.data.water_depth}m flood depth`,
            type: 'drone'
          });
          // Synchronize evacuation routes with latest drone obstacle
          fetch(`${API_BASE}/routes/evacuation`).then(r => r.ok ? r.json() : []).then(data => {
            if (Array.isArray(data) && data.length > 0) setEvacuationRoutes(data);
          }).catch(()=>{});
        } else if (msg.event === 'ROUTES_UPDATED') {
          if (Array.isArray(msg.data)) {
            setEvacuationRoutes(msg.data);
          }
          setLiveBanner({
            title: '🛣️ Evacuation Paths Recalculated',
            text: msg.message || 'Safe evacuation corridors updated with live hazard intelligence.',
            type: 'route'
          });
          setStatusMessage({ text: 'Evacuation corridors recalculated', type: 'success' });
        } else if (msg.event === 'DEMO_DATA_REFRESHED') {
          fetchAllData();
          setLiveBanner({
            title: '🔄 Simulation Scenario Synchronized',
            text: msg.message || 'All disaster indicators reloaded from server.',
            type: 'info'
          });
        } else if (msg.event === 'RELIEF_CAMP_UPDATED') {
          if (msg.data) {
            setReliefCamps(prev => {
              const exists = prev.some(c => c.id === msg.data.id);
              if (exists) {
                return prev.map(c => c.id === msg.data.id ? msg.data : c);
              }
              return [msg.data, ...prev];
            });
          }
          setLiveBanner({
            title: '⛺ Relief Camp Updated',
            text: msg.message || 'Camp occupancy / shelter status updated.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'NEW_RELIEF_REQUEST') {
          if (msg.data) {
            setReliefRequests(prev => [msg.data, ...prev]);
          }
          setLiveBanner({
            title: '📦 New Relief Request',
            text: msg.message || 'New humanitarian supply request received.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'RELIEF_REQUEST_UPDATED') {
          if (msg.data) {
            setReliefRequests(prev => prev.map(r => r.id === msg.data.id ? msg.data : r));
          }
          setLiveBanner({
            title: '📋 Relief Request Updated',
            text: msg.message || 'Request status updated.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'RESOURCE_UPDATED') {
          if (msg.data) {
            setReliefResources(prev => prev.map(r => r.id === msg.data.id ? msg.data : r));
          }
          setLiveBanner({
            title: '📦 Resource Stock Updated',
            text: msg.message || 'Supply inventory quantity updated.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'RELIEF_TEAM_UPDATED') {
          if (msg.data) {
            setReliefTeams(prev => prev.map(t => t.id === msg.data.id ? msg.data : t));
          }
          setLiveBanner({
            title: '🚒 Relief Team Status Updated',
            text: msg.message || 'Team coordinates/status updated.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'RECOVERY_UPDATED') {
          if (msg.data) {
            setRecoveryItems(prev => prev.map(i => i.id === msg.data.id ? msg.data : i));
          }
          setLiveBanner({
            title: '🏗️ Infrastructure Recovery Progress',
            text: msg.message || 'Reconstruction milestone recorded.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'DAMAGE_ASSESSMENT_UPDATED') {
          if (msg.data) {
            setDamageAssessments(prev => prev.map(d => d.zone_id === msg.data.zone_id ? msg.data : d));
          }
          setLiveBanner({
            title: '📑 Damage Assessment Updated',
            text: msg.message || 'Sector damage report refreshed.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/summary`).then(r => r.ok ? r.json() : null).then(s => s && setReliefSummary(s)).catch(()=>{});
        } else if (msg.event === 'NEW_DONATION') {
          if (msg.data) {
            setReliefDonations(prev => [msg.data, ...prev]);
            setReliefFund(prev => prev ? {
              ...prev,
              raised_amount: prev.raised_amount + (msg.data.amount || 0),
              total_donors: prev.total_donors + 1
            } : prev);
          }
          setLiveBanner({
            title: '💰 New Relief Contribution Received!',
            text: msg.message || 'Demographic contribution recorded.',
            type: 'relief'
          });
          fetch(`${API_BASE}/relief/funds`).then(r => r.ok ? r.json() : null).then(f => f && setReliefFund(f)).catch(()=>{});
        }

      } catch (err) {
        console.error('Error processing live WebSocket message:', err);
      }
    };

    socket.onerror = (err) => {
      console.warn('[RakshaNet] WebSocket transport notice:', err);
    };

    socket.onclose = (event) => {
      console.warn(`[RakshaNet] WebSocket closed (code: ${event.code}). Auto-reconnecting...`);
      setWsStatus('RECONNECTING');
      wsRef.current = null;

      reconnectAttemptsRef.current += 1;
      const delay = Math.min(8000, 1200 * Math.pow(1.3, reconnectAttemptsRef.current));
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, delay);
    };
  }, [fetchAllData]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connectWebSocket]);

  // Auto-dismiss live event notification banner after 6 seconds
  useEffect(() => {
    if (liveBanner) {
      const timer = setTimeout(() => setLiveBanner(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [liveBanner]);

  // Recalculate AI Risk
  const handleRecalculateRisk = async () => {
    try {
      setIsRecalculating(true);
      setStatusMessage({ text: 'AI Risk Engine recalculating sectors...', type: 'info' });
      const res = await fetch(`${API_BASE}/zone-intelligence/recalculate`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setIntelligence(data);
        setStatusMessage({ text: 'AI Risk & Priority scores successfully updated!', type: 'success' });
      }
    } catch (err) {
      setStatusMessage({ text: 'Error triggering AI recalculation', type: 'error' });
    } finally {
      setIsRecalculating(false);
    }
  };

  // Phase 7: Recalculate Evacuation Routes
  const handleRecalculateRoutes = async () => {
    try {
      setIsRecalculatingRoutes(true);
      setStatusMessage({ text: 'AI Route Engine computing optimal safe paths & bypassing flooded chokepoints...', type: 'info' });
      const res = await fetch(`${API_BASE}/routes/recalculate`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setEvacuationRoutes(data);
        setStatusMessage({ text: `Successfully recomputed ${data.length} safe evacuation corridors!`, type: 'success' });
      }
    } catch (err) {
      console.error('Error recalculating evacuation routes:', err);
      setStatusMessage({ text: 'Error recalculating evacuation routes', type: 'error' });
    } finally {
      setIsRecalculatingRoutes(false);
    }
  };


  // Seed Demo Data
  const handleSeedDemo = async () => {
    try {
      setIsLoading(true);
      setStatusMessage({ text: 'Resetting and seeding Krishna Delta scenario data...', type: 'info' });
      const res = await fetch(`${API_BASE}/demo/seed`, { method: 'POST' });
      if (res.ok) {
        await fetchAllData();
        setStatusMessage({ text: 'Krishna Delta demonstration scenario loaded successfully!', type: 'success' });
      }
    } catch (err) {
      setStatusMessage({ text: 'Error seeding demo data', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // Simulate Live Event (Demo Verification Helper)
  const handleSimulateLiveEvent = async (type = 'sos') => {
    try {
      setIsSimulatingEvent(true);
      setStatusMessage({ text: `Broadcasting simulated live ${type.toUpperCase()} incident via WebSocket...`, type: 'info' });
      const res = await fetch(`${API_BASE}/demo/simulate-live-event?event_type=${type}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        console.log('Live simulation broadcasted:', data);
      }
    } catch (err) {
      console.error('Error triggering simulated live event:', err);
    } finally {
      setIsSimulatingEvent(false);
    }
  };


  // -------------------------------------------------------------------
  // METRICS COMPUTATION
  // -------------------------------------------------------------------
  const metrics = useMemo(() => {
    const totalPopulation = intelligence.reduce((acc, z) => acc + (z.affected_population || z.population || 0), 0);
    const highRiskZones = intelligence.filter(z => z.risk_level === 'RED' || z.risk_level === 'ORANGE').length;
    const criticalSOS = sosReports.filter(s => s.urgency === 'critical').length;
    const blockedRoads = droneReadings.filter(d => d.road_status === 'blocked').length;

    return {
      totalZones: intelligence.length || 7,
      highRiskZones,
      totalPopulation,
      totalSOS: sosReports.length,
      criticalSOS,
      blockedRoads,
      activeAlerts: alerts.length
    };
  }, [intelligence, sosReports, droneReadings, alerts]);

  // -------------------------------------------------------------------
  // LEAFLET MAP INITIALIZATION & UPDATES (RESILIENT)
  // -------------------------------------------------------------------
  useEffect(() => {
    if (!mapRef.current) return;

    try {
      if (!leafletMapRef.current) {
        // Prevent duplicate initialization on same container
        if (mapRef.current._leaflet_id) {
          mapRef.current._leaflet_id = null;
        }

        // Initialize map centered on Krishna River Delta (Vijayawada)
        const map = L.map(mapRef.current, {
          center: [16.506, 80.638],
          zoom: 13,
          zoomControl: false
        });

        L.control.zoom({ position: 'bottomright' }).addTo(map);

        // Dark CartoDB Map Tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
          subdomains: 'abcd',
          maxZoom: 19
        }).addTo(map);

        leafletMapRef.current = map;
      }

      const map = leafletMapRef.current;

      // Clear existing markers & shapes safely
      markersRef.current.circles.forEach(c => { try { c.remove(); } catch(e){} });
      markersRef.current.zones.forEach(m => { try { m.remove(); } catch(e){} });
      markersRef.current.drones.forEach(d => { try { d.remove(); } catch(e){} });
      markersRef.current.sos.forEach(s => { try { s.remove(); } catch(e){} });
      markersRef.current = { zones: [], drones: [], sos: [], circles: [] };

      // 1. Render Zone Polygons / Circles & Centroids
      if (layerVisibility.zones && intelligence.length > 0) {
        intelligence.forEach(zone => {
          const lat = typeof zone.latitude === 'number' && !isNaN(zone.latitude)
            ? zone.latitude
            : (ZONE_COORDINATES[zone.zone_id]?.[0] || 16.506);
          const lon = typeof zone.longitude === 'number' && !isNaN(zone.longitude)
            ? zone.longitude
            : (ZONE_COORDINATES[zone.zone_id]?.[1] || 80.638);

          if (typeof lat !== 'number' || typeof lon !== 'number' || isNaN(lat) || isNaN(lon)) return;

          const color = RISK_COLORS[zone.risk_level]?.hex || '#ef4444';
          const isSevere = zone.risk_level === 'RED';
          const riskScoreNum = Number(zone.risk_score != null ? zone.risk_score : 50);

          // Zone Radius Circle Overlay
          const circle = L.circle([lat, lon], {
            radius: 1200,
            color: color,
            weight: isSevere ? 2 : 1.5,
            fillColor: color,
            fillOpacity: isSevere ? 0.25 : 0.15,
            dashArray: isSevere ? null : '4, 4'
          }).addTo(map);

          circle.bindPopup(`
            <div class="p-1">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-2 mb-2">
                <span class="font-bold text-white text-sm">${zone.zone_name || 'Zone'}</span>
                <span class="px-2 py-0.5 text-xs font-bold rounded ${RISK_COLORS[zone.risk_level]?.badge || 'bg-red-600'} text-white">
                  ${zone.risk_level || 'WATCH'}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                <div><span class="text-slate-400">Risk Score:</span> <span class="font-bold text-white">${riskScoreNum.toFixed(1)}/100</span></div>
                <div><span class="text-slate-400">Priority Rank:</span> <span class="font-bold text-amber-400">#${zone.response_priority_rank || zone.priority_rank || 1}</span></div>
                <div><span class="text-slate-400">Trajectory:</span> <span class="font-semibold text-slate-200 capitalize">${zone.overall_trajectory || 'worsening'}</span></div>
                <div><span class="text-slate-400">Active SOS:</span> <span class="font-bold text-red-400">${zone.active_sos_count || 0}</span></div>
              </div>
              <div class="bg-slate-900/80 p-2 rounded border border-slate-700 text-xs">
                <div class="text-slate-400 text-[10px] uppercase font-semibold">AI Recommended Action</div>
                <div class="font-bold text-amber-300 mt-0.5">${zone.recommended_action || 'MONITOR CLOSELY'}</div>
              </div>
            </div>
          `);

          // Zone Centroid Badge Marker
          const zoneIcon = L.divIcon({
            className: 'custom-zone-icon-container',
            html: `
              <div class="custom-zone-marker ${isSevere ? 'pulse-red' : ''}" style="background-color: ${color}; width: 34px; height: 34px;">
                #${zone.response_priority_rank || zone.priority_rank || 1}
              </div>
            `,
            iconSize: [34, 34],
            iconAnchor: [17, 17]
          });

          const marker = L.marker([lat, lon], { icon: zoneIcon }).addTo(map);
          marker.on('click', () => {
            setSelectedZone(zone);
            circle.openPopup();
          });

          markersRef.current.circles.push(circle);
          markersRef.current.zones.push(marker);
        });
      }

      // 2. Render Drone Telemetry Markers (Road Obstacles & Water Depth)
      if (layerVisibility.drones && droneReadings.length > 0) {
        droneReadings.forEach(drone => {
          if (typeof drone.latitude !== 'number' || typeof drone.longitude !== 'number' || isNaN(drone.latitude) || isNaN(drone.longitude)) return;

          const isBlocked = drone.road_status === 'blocked';
          const isRestricted = drone.road_status === 'restricted';
          const statusColor = isBlocked ? '#ef4444' : isRestricted ? '#f97316' : '#22c55e';
          const obstacleLabel = (drone.obstacle_type || 'obstacle').replace('_', ' ');
          const depthVal = Number(drone.water_depth != null ? drone.water_depth : 0);

          const droneIcon = L.divIcon({
            className: 'custom-drone-icon-container',
            html: `
              <div class="custom-drone-marker" style="border-color: ${statusColor}; width: 28px; height: 28px;">
                <svg class="w-4 h-4" fill="none" stroke="${statusColor}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          });

          const marker = L.marker([drone.latitude, drone.longitude], { icon: droneIcon }).addTo(map);
          marker.bindPopup(`
            <div class="p-1">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-sky-400 text-xs flex items-center gap-1">
                  <span>🚁</span> Drone Survey Telemetry
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${isBlocked ? 'bg-red-600' : isRestricted ? 'bg-orange-600' : 'bg-emerald-600'} text-white">
                  ${drone.road_status || 'Survey'}
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">Obstacle:</span> <span class="font-semibold text-white capitalize">${obstacleLabel}</span></div>
                <div><span class="text-slate-400">Water Depth:</span> <span class="font-bold text-amber-400">${depthVal.toFixed(1)} meters</span></div>
                <div><span class="text-slate-400">Confidence:</span> <span class="text-slate-300">${((drone.confidence || 0.9) * 100).toFixed(0)}%</span></div>
              </div>
            </div>
          `);
          markersRef.current.drones.push(marker);
        });
      }

      // 3. Render Citizen SOS Distress Markers
      if (layerVisibility.sos && sosReports.length > 0) {
        sosReports.forEach(sos => {
          if (typeof sos.latitude !== 'number' || typeof sos.longitude !== 'number' || isNaN(sos.latitude) || isNaN(sos.longitude)) return;

          const uColor = URGENCY_COLORS[sos.urgency]?.hex || '#ef4444';
          const isCritical = sos.urgency === 'critical';
          const extraction = sos.structured_extraction || {};

          const sosIcon = L.divIcon({
            className: 'custom-sos-icon-container',
            html: `
              <div class="custom-sos-marker ${isCritical ? 'pulse-red' : ''}" style="background-color: ${uColor}; width: 26px; height: 26px;">
                <span class="text-white font-bold text-[11px]">SOS</span>
              </div>
            `,
            iconSize: [26, 26],
            iconAnchor: [13, 13]
          });

          const marker = L.marker([sos.latitude, sos.longitude], { icon: sosIcon }).addTo(map);
          marker.bindPopup(`
            <div class="p-1 max-w-[260px]">
              <div class="flex items-center justify-between gap-1 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-red-400 text-xs flex items-center gap-1">
                  <span>🚨</span> Citizen Distress Signal
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${URGENCY_COLORS[sos.urgency]?.badge || 'bg-red-600'} text-white">
                  ${sos.urgency || 'high'}
                </span>
              </div>
              <p class="text-xs text-slate-200 italic bg-slate-900/90 p-2 rounded border border-slate-700 mb-2">
                "${sos.message || ''}"
              </p>
              <div class="grid grid-cols-2 gap-1 text-[11px] text-slate-300">
                <div><span class="text-slate-400">Language:</span> <span class="font-semibold text-white uppercase">${extraction.detected_language || sos.language || 'en'}</span></div>
                <div><span class="text-slate-400">Need:</span> <span class="font-semibold text-amber-400 capitalize">${sos.need_type || 'rescue'}</span></div>
                <div><span class="text-slate-400">Priority:</span> <span class="font-bold text-red-400">${sos.priority_score || 50}/100</span></div>
                <div><span class="text-slate-400">People:</span> <span class="font-semibold text-white">${extraction.people_count || 'Unknown'}</span></div>
              </div>
              ${extraction.danger_factors && extraction.danger_factors.length > 0 ? `
                <div class="mt-2 flex flex-wrap gap-1">
                  ${extraction.danger_factors.map(df => `
                    <span class="px-1 py-0.5 text-[9px] bg-red-950 text-red-300 border border-red-800 rounded">
                      ${df.replace(/_/g, ' ')}
                    </span>
                  `).join('')}
                </div>
              ` : ''}
            </div>
          `);
          markersRef.current.sos.push(marker);
        });
      }
    } catch (mapErr) {
      console.error('[RakshaNet Leaflet Render Warning]', mapErr);
    }
  }, [intelligence, droneReadings, sosReports, layerVisibility]);

  // -------------------------------------------------------------------
  // PHASE 7 – ROUTE LAYER RENDERING (Evacuation & Drone Recon Polylines)
  // -------------------------------------------------------------------
  useEffect(() => {
    if (!leafletMapRef.current) return;
    const map = leafletMapRef.current;

    // Clear existing route layers
    routeLayersRef.evacuation.forEach(l => { try { l.remove(); } catch(e){} });
    routeLayersRef.altRoutes.forEach(l => { try { l.remove(); } catch(e){} });
    routeLayersRef.droneRecon.forEach(l => { try { l.remove(); } catch(e){} });
    routeLayersRef.shelters.forEach(l => { try { l.remove(); } catch(e){} });
    routeLayersRef.evacuation.length = 0;
    routeLayersRef.altRoutes.length = 0;
    routeLayersRef.droneRecon.length = 0;
    routeLayersRef.shelters.length = 0;

    try {
      // 1. RECOMMENDED EVACUATION ROUTE POLYLINES (green dashed/solid)
      if (layerVisibility.evacuation && evacuationRoutes.length > 0) {
        evacuationRoutes.forEach((route, idx) => {
          const coords = route.waypoints;
          if (!Array.isArray(coords) || coords.length < 2) return;

          const safetyColor = route.safety_score >= 80 ? '#10b981' : route.safety_score >= 60 ? '#f59e0b' : '#ef4444';

          const polyline = L.polyline(coords, {
            color: safetyColor,
            weight: 4,
            opacity: 0.90,
            dashArray: '8, 5',
          }).addTo(map);

          polyline.bindPopup(`
            <div class="p-1 max-w-[270px]">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-emerald-400 text-xs flex items-center gap-1">
                  <span>🛣️</span> Recommended Safe Route
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${route.status === 'OPTIMAL_SAFE' ? 'bg-emerald-700' : 'bg-amber-700'} text-white">
                  ${route.route_risk_level ? route.route_risk_level + ' RISK' : 'SAFE'}
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">From:</span> <span class="font-semibold text-white">${route.origin_name}</span></div>
                <div><span class="text-slate-400">Nearest Shelter:</span> <span class="font-semibold text-emerald-300">${route.destination_name}</span></div>
                <div><span class="text-slate-400">Distance:</span> <span class="font-bold text-white">${route.distance_km} km</span></div>
                <div><span class="text-slate-400">ETA:</span> <span class="font-bold text-amber-400">${route.estimated_time_minutes} min</span></div>
                <div><span class="text-slate-400">Safety Index:</span> <span class="font-bold" style="color:${safetyColor}">${route.safety_score}/100</span></div>
                <div><span class="text-slate-400">Route Risk:</span> <span class="font-bold text-emerald-400">${route.route_risk_level || 'LOW'}</span></div>
                ${route.hazards_avoided && route.hazards_avoided.length > 0 ? `<div class="text-amber-300 text-[10px] pt-0.5">⚠️ ${route.hazards_avoided.length} hazard(s) bypassed</div>` : ''}
                ${route.corridor_notes && route.corridor_notes.length > 0 ? `<div class="text-sky-300 text-[10px]">ℹ️ ${route.corridor_notes[0]}</div>` : ''}
              </div>
            </div>
          `);

          // Route ID label at midpoint
          const midIdx = Math.floor(coords.length / 2);
          const midCoord = coords[midIdx];
          if (midCoord) {
            const labelIcon = L.divIcon({
              className: '',
              html: `<div style="background:#10b981cc;color:#fff;font-size:9px;font-weight:bold;padding:2px 5px;border-radius:4px;white-space:nowrap;border:1px solid #10b981;">RECOMMENDED #${idx + 1}</div>`,
              iconAnchor: [28, 8]
            });
            const label = L.marker(midCoord, { icon: labelIcon, interactive: false }).addTo(map);
            routeLayersRef.evacuation.push(label);
          }

          routeLayersRef.evacuation.push(polyline);

          // 1b. ALTERNATIVE EVACUATION ROUTE POLYLINES (amber dashed)
          if (layerVisibility.alternativeRoutes && route.alternative_route && Array.isArray(route.alternative_route.waypoints) && route.alternative_route.waypoints.length >= 2) {
            const altCoords = route.alternative_route.waypoints;
            const altPolyline = L.polyline(altCoords, {
              color: '#f59e0b',
              weight: 2.5,
              opacity: 0.75,
              dashArray: '4, 8',
            }).addTo(map);

            altPolyline.bindPopup(`
              <div class="p-1 max-w-[270px]">
                <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                  <span class="font-bold text-amber-400 text-xs flex items-center gap-1">
                    <span>🔀</span> Alternative Backup Route
                  </span>
                  <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase bg-amber-700 text-white">
                    ALT ROUTE
                  </span>
                </div>
                <div class="text-xs space-y-1">
                  <div><span class="text-slate-400">From:</span> <span class="font-semibold text-white">${route.origin_name}</span></div>
                  <div><span class="text-slate-400">Backup Shelter:</span> <span class="font-semibold text-amber-300">${route.alternative_route.destination_name}</span></div>
                  <div><span class="text-slate-400">Distance:</span> <span class="font-bold text-white">${route.alternative_route.distance_km} km</span></div>
                  <div><span class="text-slate-400">ETA:</span> <span class="font-bold text-amber-400">${route.alternative_route.estimated_time_minutes} min</span></div>
                  <div><span class="text-slate-400">Safety Index:</span> <span class="font-bold text-amber-400">${route.alternative_route.safety_score}/100</span></div>
                  <div class="text-slate-400 text-[10px] pt-1 border-t border-slate-700/60">ℹ️ Standby backup corridor if primary route faces traffic congestion or water rise.</div>
                </div>
              </div>
            `);
            routeLayersRef.altRoutes.push(altPolyline);
          }
        });


        // Shelter Markers
        const shelterIcon = (name) => L.divIcon({
          className: '',
          html: `<div style="background:#10b981;color:#fff;font-size:10px;font-weight:900;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 0 8px #10b98180;">⛺</div>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        });

        const shelterCoords = [
          { lat: 16.4800, lon: 80.6020, name: 'Tadepalli Primary Relief Haven', cap: 15000, occ: 4200, elev: 28.5, med: true },
          { lat: 16.5170, lon: 80.6120, name: 'Kanakadurga High-Ground Center', cap: 8000, occ: 2800, elev: 34.0, med: true },
          { lat: 16.4870, lon: 80.6720, name: 'Autonagar Industrial Elevated Shelter', cap: 6500, occ: 1900, elev: 26.0, med: false },
        ];
        shelterCoords.forEach(s => {
          const sm = L.marker([s.lat, s.lon], { icon: shelterIcon(s.name) }).addTo(map);
          sm.bindPopup(`
            <div class="p-1">
              <div class="font-bold text-emerald-400 text-xs border-b border-slate-700 pb-1 mb-1.5">⛺ Relief Haven</div>
              <div class="text-xs space-y-1">
                <div class="font-bold text-white">${s.name}</div>
                <div><span class="text-slate-400">Capacity:</span> <span class="font-semibold">${s.cap.toLocaleString()}</span></div>
                <div><span class="text-slate-400">Occupied:</span> <span class="font-semibold text-amber-300">${s.occ.toLocaleString()}</span></div>
                <div><span class="text-slate-400">Elevation:</span> <span class="font-semibold text-sky-300">${s.elev} m ASL</span></div>
                <div><span class="text-slate-400">Medical:</span> <span class="font-semibold ${s.med ? 'text-emerald-400' : 'text-slate-400'}">${s.med ? '✅ Available' : '—'}</span></div>
                <div class="px-2 py-0.5 bg-emerald-900 text-emerald-300 rounded text-[10px] font-bold text-center mt-1">OPEN – RECEIVING EVACUEES</div>
              </div>
            </div>
          `);
          routeLayersRef.shelters.push(sm);
        });
      }

      // 2. DRONE RECON FLIGHT PATHS (cyan)
      if (layerVisibility.droneRoutes && droneReconMissions.length > 0) {
        const droneColors = ['#06b6d4', '#a78bfa'];
        droneReconMissions.forEach((mission, idx) => {
          const path = mission.flight_path;
          if (!Array.isArray(path) || path.length < 2) return;
          const color = droneColors[idx % droneColors.length];

          const poly = L.polyline(path, {
            color,
            weight: 2.5,
            opacity: 0.80,
            dashArray: '4, 6',
          }).addTo(map);

          poly.bindPopup(`
            <div class="p-1 max-w-[260px]">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-sky-400 text-xs flex items-center gap-1">
                  <span>🚁</span> ${mission.mission_id}
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">Drone:</span> <span class="font-semibold text-white">${mission.drone_callsign}</span></div>
                <div><span class="text-slate-400">Base:</span> <span class="font-semibold text-slate-200">${mission.base_hub}</span></div>
                <div><span class="text-slate-400">Distance:</span> <span class="font-bold text-white">${mission.total_distance_km} km</span></div>
                <div><span class="text-slate-400">ETA:</span> <span class="font-bold text-amber-400">${mission.estimated_flight_minutes} min</span></div>
                <div><span class="text-slate-400">Objective:</span> <span class="text-sky-300 text-[10px]">${mission.mission_objective}</span></div>
              </div>
            </div>
          `);

          // Drone base marker
          const firstCoord = path[0];
          if (firstCoord) {
            const baseIcon = L.divIcon({
              className: '',
              html: `<div style="background:${color}cc;color:#fff;font-size:11px;font-weight:900;width:26px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;border:2px solid ${color};box-shadow:0 0 6px ${color}80;">🚁</div>`,
              iconSize: [26, 26],
              iconAnchor: [13, 13]
            });
            const baseMarker = L.marker(firstCoord, { icon: baseIcon }).addTo(map);
            baseMarker.bindPopup(`<div class="text-xs font-bold text-sky-300 p-1">${mission.drone_callsign}<br/><span class="text-slate-400 font-normal text-[10px]">${mission.base_hub}</span></div>`);
            routeLayersRef.droneRecon.push(baseMarker);
          }

          routeLayersRef.droneRecon.push(poly);
        });
      }
    } catch (routeErr) {
      console.error('[RakshaNet Route Layer Error]', routeErr);
    }
  }, [evacuationRoutes, droneReconMissions, layerVisibility.evacuation, layerVisibility.alternativeRoutes, layerVisibility.droneRoutes]);

  // -------------------------------------------------------------------
  // PHASE 8 – RELIEF & RECOVERY LAYER RENDERING (Camps, Teams, Recovery Sites)
  // -------------------------------------------------------------------
  useEffect(() => {
    if (!leafletMapRef.current) return;
    const map = leafletMapRef.current;

    // Clear existing relief layers
    reliefLayersRef.camps.forEach(l => { try { l.remove(); } catch(e){} });
    reliefLayersRef.teams.forEach(l => { try { l.remove(); } catch(e){} });
    reliefLayersRef.recovery.forEach(l => { try { l.remove(); } catch(e){} });
    reliefLayersRef.camps.length = 0;
    reliefLayersRef.teams.length = 0;
    reliefLayersRef.recovery.length = 0;

    try {
      // 1. Designated Relief Camps (Tents)
      if (layerVisibility.camps && reliefCamps.length > 0) {
        reliefCamps.forEach(camp => {
          if (typeof camp.latitude !== 'number' || typeof camp.longitude !== 'number' || isNaN(camp.latitude) || isNaN(camp.longitude)) return;

          const occRatio = camp.current_occupancy / floatSafe(camp.capacity);
          const statusBg = camp.status === 'Full' ? 'bg-red-600' : camp.status === 'Near Capacity' ? 'bg-amber-600' : 'bg-emerald-600';

          const campIcon = L.divIcon({
            className: 'custom-camp-icon-container',
            html: `
              <div class="custom-camp-marker" style="width: 30px; height: 30px;">
                ⛺
              </div>
            `,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
          });

          const marker = L.marker([camp.latitude, camp.longitude], { icon: campIcon }).addTo(map);
          marker.bindPopup(`
            <div class="p-1 max-w-[270px]">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-emerald-400 text-xs flex items-center gap-1">
                  <span>⛺</span> ${camp.name}
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${statusBg} text-white">
                  ${camp.status}
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">Location:</span> <span class="text-white">${camp.location_name || 'Krishna Sector'}</span></div>
                <div><span class="text-slate-400">Capacity:</span> <span class="font-bold text-white">${camp.capacity.toLocaleString()} persons</span></div>
                <div><span class="text-slate-400">Occupancy:</span> <span class="font-bold text-amber-300">${camp.current_occupancy.toLocaleString()} (${Math.round(occRatio * 100)}%)</span></div>
                <div><span class="text-slate-400">Available Beds:</span> <span class="font-bold text-emerald-400">${camp.available_beds}</span></div>
                <div><span class="text-slate-400">Contact:</span> <span class="text-slate-200">${camp.contact_person || 'Field Officer'} (${camp.contact_phone || 'Emergency Grid'})</span></div>
                <div class="flex items-center gap-2 text-[10px] pt-1">
                  <span class="${camp.medical_facility ? 'text-emerald-400' : 'text-slate-500'}">🏥 Med Clinic: ${camp.medical_facility ? 'Yes' : 'No'}</span>
                  <span class="${camp.food_supply_status === 'Adequate' ? 'text-emerald-400' : 'text-amber-400'}">🍲 Food: ${camp.food_supply_status || 'Adequate'}</span>
                  <span class="${camp.water_supply_status === 'Adequate' ? 'text-emerald-400' : 'text-amber-400'}">💧 Water: ${camp.water_supply_status || 'Adequate'}</span>
                </div>
              </div>
            </div>
          `);
          reliefLayersRef.camps.push(marker);
        });
      }

      // 2. Relief Teams (Vehicles / Badges)
      if (layerVisibility.reliefTeams && reliefTeams.length > 0) {
        reliefTeams.forEach(team => {
          if (typeof team.latitude !== 'number' || typeof team.longitude !== 'number' || isNaN(team.latitude) || isNaN(team.longitude)) return;

          const teamIcon = L.divIcon({
            className: 'custom-team-icon-container',
            html: `
              <div class="custom-team-marker" style="width: 28px; height: 28px;">
                🚒
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          });

          const marker = L.marker([team.latitude, team.longitude], { icon: teamIcon }).addTo(map);
          marker.bindPopup(`
            <div class="p-1 max-w-[260px]">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-blue-400 text-xs flex items-center gap-1">
                  <span>🚒</span> ${team.name}
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${team.status === 'Deployed' ? 'bg-blue-600' : team.status === 'En Route' ? 'bg-amber-600' : 'bg-emerald-600'} text-white">
                  ${team.status}
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">Type:</span> <span class="font-semibold text-white capitalize">${team.team_type}</span></div>
                <div><span class="text-slate-400">Members:</span> <span class="font-bold text-white">${team.members_count} personnel</span></div>
                <div><span class="text-slate-400">Leader:</span> <span class="text-slate-200">${team.leader_name}</span></div>
                <div><span class="text-slate-400">Task:</span> <span class="text-sky-300 font-medium">${team.assigned_task || 'Patrol & Assessment'}</span></div>
              </div>
            </div>
          `);
          reliefLayersRef.teams.push(marker);
        });
      }

      // 3. Infrastructure Recovery Sites (Tools)
      if (layerVisibility.recovery && recoveryItems.length > 0) {
        recoveryItems.forEach(item => {
          if (typeof item.latitude !== 'number' || typeof item.longitude !== 'number' || isNaN(item.latitude) || isNaN(item.longitude)) return;

          const recIcon = L.divIcon({
            className: 'custom-recovery-icon-container',
            html: `
              <div class="custom-recovery-marker" style="width: 28px; height: 28px;">
                🏗️
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          });

          const marker = L.marker([item.latitude, item.longitude], { icon: recIcon }).addTo(map);
          marker.bindPopup(`
            <div class="p-1 max-w-[270px]">
              <div class="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-2">
                <span class="font-bold text-amber-400 text-xs flex items-center gap-1">
                  <span>🏗️</span> ${item.name}
                </span>
                <span class="px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${item.recovery_status === 'Restored' ? 'bg-emerald-700' : item.recovery_status === 'Under Repair' ? 'bg-amber-700' : 'bg-red-700'} text-white">
                  ${item.progress_pct}%
                </span>
              </div>
              <div class="text-xs space-y-1">
                <div><span class="text-slate-400">Category:</span> <span class="font-semibold text-white capitalize">${item.category}</span></div>
                <div><span class="text-slate-400">Status:</span> <span class="font-bold text-amber-300">${item.recovery_status}</span></div>
                <div><span class="text-slate-400">Agency:</span> <span class="text-slate-200">${item.responsible_agency || 'AP Disaster Mgmt'}</span></div>
                <div><span class="text-slate-400">Est. Completion:</span> <span class="text-sky-300">${item.estimated_restoration || 'In progress'}</span></div>
                <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1.5">
                  <div class="h-full bg-amber-500" style="width: ${item.progress_pct}%"></div>
                </div>
              </div>
            </div>
          `);
          reliefLayersRef.recovery.push(marker);
        });
      }
    } catch (reliefErr) {
      console.error('[RakshaNet Relief Layer Error]', reliefErr);
    }
  }, [reliefCamps, reliefTeams, recoveryItems, layerVisibility.camps, layerVisibility.reliefTeams, layerVisibility.recovery]);

  // Helper for float division safe
  const floatSafe = (val) => (typeof val === 'number' && val > 0) ? val : 1;


  // Fly map to selected zone with fallback coordinates
  const flyToZone = (zone) => {

    setSelectedZone(zone);
    const lat = typeof zone.latitude === 'number' && !isNaN(zone.latitude)
      ? zone.latitude
      : (ZONE_COORDINATES[zone.zone_id]?.[0] || 16.506);
    const lon = typeof zone.longitude === 'number' && !isNaN(zone.longitude)
      ? zone.longitude
      : (ZONE_COORDINATES[zone.zone_id]?.[1] || 80.638);

    if (leafletMapRef.current && !isNaN(lat) && !isNaN(lon)) {
      leafletMapRef.current.flyTo([lat, lon], 14, { duration: 1.2 });
    }
  };


  // Filtered SOS reports
  const filteredSOS = useMemo(() => {
    return sosReports.filter(report => {
      const ext = report.structured_extraction || {};
      const lang = ext.detected_language || report.language || 'en';
      const matchesLang = sosLangFilter === 'ALL' || lang === sosLangFilter;
      const matchesUrgency = sosUrgencyFilter === 'ALL' || report.urgency === sosUrgencyFilter;
      return matchesLang && matchesUrgency;
    });
  }, [sosReports, sosLangFilter, sosUrgencyFilter]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      
      {/* 1. TOP HEADER & SYSTEM STATUS */}
      <header className="h-16 bg-slate-900/90 border-b border-slate-800 px-4 flex items-center justify-between shrink-0 shadow-lg z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-sky-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <span className="text-xl">🛡️</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                RakshaNet
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase tracking-wide">
                SIH Prototype
              </span>
              
              {/* WebSocket Live Status Indicator */}
              {wsStatus === 'CONNECTED' ? (
                <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-bold bg-emerald-950/70 border border-emerald-700/80 px-2.5 py-0.5 rounded-full shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  Live WebSockets: Connected
                </span>
              ) : wsStatus === 'RECONNECTING' ? (
                <span className="flex items-center gap-1.5 text-[11px] text-amber-400 font-bold bg-amber-950/70 border border-amber-700/80 px-2.5 py-0.5 rounded-full shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
                  WebSockets: Reconnecting...
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[11px] text-red-400 font-bold bg-red-950/70 border border-red-700/80 px-2.5 py-0.5 rounded-full shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  WebSockets: Disconnected
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              Krishna River Delta Basin (Vijayawada-Amaravati Coordination Sector)
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const nextState = !isSimulatedOffline;
              setIsSimulatedOffline(nextState);
              if (nextState) {
                setLiveBanner({
                  title: '⚡ SIMULATED OFFLINE MODE ACTIVATED',
                  text: 'Network connection toggled to simulated offline for SIH demonstration. Operating strictly on local cached emergency snapshot.',
                  type: 'warning'
                });
              } else {
                setLiveBanner({
                  title: '🌐 LIVE NETWORK STREAM RESTORED',
                  text: 'Restored live online connection to RakshaNet Operations Grid. Resynchronizing backend services...',
                  type: 'info'
                });
                fetchAllData();
              }
            }}
            className={`px-3 py-1.5 text-xs font-extrabold rounded-lg border transition-all flex items-center gap-1.5 shadow-md ${
              (!isOnline || isSimulatedOffline)
                ? 'bg-amber-600 hover:bg-amber-500 text-black border-amber-400 shadow-amber-600/30 animate-pulse'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
            }`}
            title="Toggle simulated network disconnection for SIH Offline Alert System demonstration"
          >
            <span>{(!isOnline || isSimulatedOffline) ? '⚡ OFFLINE MODE' : '🌐 SIMULATE OFFLINE'}</span>
          </button>
          <button
            onClick={() => handleSimulateLiveEvent('sos')}
            disabled={isSimulatingEvent}
            className="px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all disabled:opacity-50"
            title="Injects a simulated live SOS event and pushes it over WebSocket without page refresh"
          >
            <span className={isSimulatingEvent ? 'animate-spin' : ''}>⚡</span>
            {isSimulatingEvent ? 'Broadcasting...' : 'Simulate Live Event'}
          </button>
          <button
            onClick={() => setShowNLPModal(true)}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5 shadow-md shadow-indigo-600/30 transition-all"
          >
            <span>💬</span> Test SOS NLP
          </button>
          <button
            onClick={handleRecalculateRisk}
            disabled={isRecalculating}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-red-600 hover:bg-red-500 text-white flex items-center gap-1.5 shadow-md shadow-red-600/30 transition-all disabled:opacity-50"
          >
            <span className={isRecalculating ? 'animate-spin' : ''}>🧠</span>
            {isRecalculating ? 'Calculating...' : 'Recalculate AI Risk'}
          </button>
          <button
            onClick={handleSeedDemo}
            disabled={isLoading}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-all"
          >
            <span>🔄</span> Seed Demo
          </button>
        </div>
      </header>


      {/* 2. EXECUTIVE METRICS STRIP */}
      <div className="bg-slate-900/60 border-b border-slate-800/80 px-4 py-2 flex items-center justify-between gap-4 overflow-x-auto text-xs shrink-0">
        <div className="flex items-center gap-6 divide-x divide-slate-800">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Monitored Sectors:</span>
            <span className="font-bold text-white text-sm">{metrics.totalZones}</span>
          </div>
          <div className="flex items-center gap-2 pl-6">
            <span className="text-slate-400">Severe Danger Zones:</span>
            <span className="font-bold text-red-400 text-sm flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              {metrics.highRiskZones}
            </span>
          </div>
          <div className="flex items-center gap-2 pl-6">
            <span className="text-slate-400">Active Citizen SOS:</span>
            <span className="font-bold text-amber-400 text-sm">{metrics.totalSOS}</span>
          </div>
          <div className="flex items-center gap-2 pl-6">
            <span className="text-slate-400">Critical Life Threats:</span>
            <span className="font-bold text-red-500 text-sm">{metrics.criticalSOS}</span>
          </div>
          <div className="flex items-center gap-2 pl-6">
            <span className="text-slate-400">Road Inundations:</span>
            <span className="font-bold text-sky-400 text-sm">{metrics.blockedRoads} Blocked</span>
          </div>
          <div className="flex items-center gap-2 pl-6">
            <span className="text-slate-400">Affected Population:</span>
            <span className="font-bold text-slate-200 text-sm">{metrics.totalPopulation.toLocaleString()}</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusMessage.type === 'error' ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
          <span>{statusMessage.text}</span>
        </div>
      </div>

      {/* 2.5 PROMINENT OFFLINE EMERGENCY ALERT BANNER & CACHED SNAPSHOT BAR */}
      {(!isOnline || isSimulatedOffline) && (
        <div className="bg-amber-950/90 border-b border-amber-500/80 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0 animate-fade-in shadow-2xl">
          <div className="flex items-center gap-2.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase bg-amber-500 text-slate-950 animate-pulse flex items-center gap-1">
              <span>⚡</span> OFFLINE MODE ACTIVE
            </span>
            <span className="font-semibold text-amber-200">
              Network connection offline. Displaying cached emergency snapshot from <strong className="text-white font-mono font-extrabold">{offlineCacheTimestamp || 'Previous Session'}</strong>.
            </span>
            <span className="text-[11px] text-amber-400/90 italic font-medium hidden lg:inline">
              (Note: Offline alerts rely on local cached data and are NOT live AI streams)
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-[11px] text-amber-300 font-mono flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              <strong>Cached Danger Sectors:</strong> {intelligence.filter(z => z.risk_level === 'RED' || z.risk_score >= 80).map(z => z.name).join(', ') || 'Krishna Riverfront, Bhavanipuram'}
            </div>
            <button
              onClick={() => {
                setIsSimulatedOffline(false);
                fetchAllData();
              }}
              className="px-2.5 py-1 text-[11px] font-extrabold rounded bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all shadow"
            >
              Sync & Reconnect 🔄
            </button>
          </div>
        </div>
      )}

      {/* 3. MAIN WORKSPACE (MAP + SIDEBAR) */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* LEFT / CENTER: LEAFLET MAP */}
        <div className="flex-1 relative h-full">
          <div ref={mapRef} className="w-full h-full z-0" />

          {/* REAL-TIME WEBSOCKET INCIDENT TOAST */}
          {liveBanner && (
            <div className="absolute top-4 right-4 z-20 max-w-sm glass-panel p-3 rounded-xl border border-emerald-500/60 shadow-2xl animate-fade-in text-xs space-y-1">
              <div className="flex items-center justify-between gap-2 border-b border-slate-700/60 pb-1">
                <span className="font-extrabold text-emerald-400 flex items-center gap-1.5 text-xs">
                  <span>📡</span> {liveBanner.title}
                </span>
                <button
                  onClick={() => setLiveBanner(null)}
                  className="text-slate-400 hover:text-white text-xs px-1"
                >
                  ✕
                </button>
              </div>
              <p className="text-slate-200 italic font-medium">{liveBanner.text}</p>
              <div className="text-[10px] text-emerald-400 font-mono pt-0.5 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Pushed via WebSocket • Instant live synchronization
              </div>
            </div>
          )}

          {/* MAP OVERLAY: LAYER TOGGLE CONTROLS */}
          <div className="absolute top-4 left-4 z-10 glass-panel p-2.5 rounded-xl shadow-2xl flex flex-col gap-2 text-xs">

            <div className="font-bold text-slate-300 text-[11px] uppercase tracking-wider pb-1 border-b border-slate-700/60">
              Map Intelligence Layers
            </div>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.zones}
                onChange={e => setLayerVisibility({ ...layerVisibility, zones: e.target.checked })}
                className="rounded border-slate-700 text-red-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Risk Zones & Centroids
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.drones}
                onChange={e => setLayerVisibility({ ...layerVisibility, drones: e.target.checked })}
                className="rounded border-slate-700 text-sky-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span> Drone Road Surveys
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.sos}
                onChange={e => setLayerVisibility({ ...layerVisibility, sos: e.target.checked })}
                className="rounded border-slate-700 text-amber-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Citizen SOS Distress
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.evacuation}
                onChange={e => setLayerVisibility({ ...layerVisibility, evacuation: e.target.checked })}
                className="rounded border-slate-700 text-emerald-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded" style={{background:'#10b981',borderStyle:'dashed',borderWidth:'1px',borderColor:'#fff'}}></span> Safe Evacuation Routes
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.alternativeRoutes}
                onChange={e => setLayerVisibility({ ...layerVisibility, alternativeRoutes: e.target.checked })}
                className="rounded border-slate-700 text-amber-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded" style={{background:'#f59e0b',borderStyle:'dashed',borderWidth:'1px',borderColor:'#fff'}}></span> Alternative Routes
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.droneRoutes}
                onChange={e => setLayerVisibility({ ...layerVisibility, droneRoutes: e.target.checked })}
                className="rounded border-slate-700 text-cyan-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded" style={{background:'#06b6d4',borderStyle:'dashed',borderWidth:'1px',borderColor:'#fff'}}></span> Drone Recon Paths
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.camps}
                onChange={e => setLayerVisibility({ ...layerVisibility, camps: e.target.checked })}
                className="rounded border-slate-700 text-emerald-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span>⛺</span> Relief Camps ({reliefCamps.length})
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.reliefTeams}
                onChange={e => setLayerVisibility({ ...layerVisibility, reliefTeams: e.target.checked })}
                className="rounded border-slate-700 text-blue-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span>🚒</span> Relief Teams ({reliefTeams.length})
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={layerVisibility.recovery}
                onChange={e => setLayerVisibility({ ...layerVisibility, recovery: e.target.checked })}
                className="rounded border-slate-700 text-amber-600 focus:ring-0"
              />
              <span className="flex items-center gap-1.5">
                <span>🏗️</span> Recovery Sites ({recoveryItems.length})
              </span>
            </label>
          </div>



          {/* MAP OVERLAY: LEGEND */}
          <div className="absolute bottom-4 left-4 z-10 glass-panel p-2.5 rounded-xl shadow-2xl text-[11px] space-y-1.5">
            <div className="font-bold text-slate-300 text-[10px] uppercase tracking-wider">Risk Level Guide</div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Severe (75+)</div>
              <div className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span> Warning (55-75)</div>
              <div className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span> Watch (30-55)</div>
              <div className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Safe Haven (&lt;30)</div>
            </div>
          </div>
        </div>

        {/* RIGHT: COORDINATION & INTELLIGENCE PANELS */}
        <div className="w-96 md:w-[480px] bg-slate-900/95 border-l border-slate-800 flex flex-col h-full shrink-0 shadow-2xl z-10">
          
          {/* Panel Navigation Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-950/60 p-1">
            <button
              onClick={() => setActiveTab('zones')}
              className={`flex-1 py-1.5 px-1 text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
                activeTab === 'zones'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>📍</span> Zones ({intelligence.length})
            </button>
            <button
              onClick={() => setActiveTab('sos')}
              className={`flex-1 py-1.5 px-1 text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
                activeTab === 'sos'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>🚨</span> SOS ({sosReports.length})
            </button>
            <button
              onClick={() => setActiveTab('telemetry')}
              className={`flex-1 py-1.5 px-1 text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
                activeTab === 'telemetry'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>📊</span> Telemetry
            </button>
            <button
              onClick={() => setActiveTab('routes')}
              className={`flex-1 py-1.5 px-1 text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
                activeTab === 'routes'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>🛣️</span> Routes
            </button>
            <button
              onClick={() => setActiveTab('relief')}
              className={`flex-1 py-1.5 px-1 text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
                activeTab === 'relief'
                  ? 'bg-emerald-800 text-white shadow-md ring-1 ring-emerald-500'
                  : 'text-emerald-400 hover:text-emerald-200'
              }`}
              title="Post-Disaster Damage Assessment, Relief Supplies, Camps & Infrastructure Recovery"
            >
              <span>🏥</span> Relief & Recovery
            </button>
          </div>



          {/* TAB CONTENT: ZONE PRIORITY LIST */}
          {activeTab === 'zones' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              
              {(!isOnline || isSimulatedOffline) && (
                <div className="p-3 rounded-xl bg-amber-950/80 border border-amber-500/60 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-bold text-amber-300">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                      ⚡ CACHED EMERGENCY DISASTER ALERTS
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {offlineCacheTimestamp || 'Cached'}
                    </span>
                  </div>
                  <p className="text-[11px] text-amber-200/90">
                    Showing local emergency cache snapshot. Live AI recalculation and WebSocket streams are paused until network connection returns.
                  </p>
                  {alerts.filter(a => a.severity === 'SEVERE' || a.severity === 'EXTREME').slice(0, 2).map((a, idx) => (
                    <div key={idx} className="p-2 rounded bg-slate-950/80 border border-amber-600/40 text-[11px]">
                      <div className="font-extrabold text-amber-400">{a.source}: {a.alert_type}</div>
                      <div className="text-slate-300 mt-0.5">{a.message}</div>
                    </div>
                  ))}
                </div>
              )}

              <div className="text-[11px] text-slate-400 flex items-center justify-between px-1">
                <span>Ranked by AI Response Priority (1 = Highest)</span>
                <span>Click sector to focus</span>
              </div>

              {intelligence.map(zone => {
                const colors = RISK_COLORS[zone.risk_level] || RISK_COLORS.RED;
                const isSelected = selectedZone?.zone_id === zone.zone_id;

                return (
                  <div
                    key={zone.zone_id}
                    onClick={() => flyToZone(zone)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-slate-800/90 border-blue-500 shadow-lg shadow-blue-500/20 ring-1 ring-blue-500'
                        : 'glass-card border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`w-6 h-6 rounded-lg flex items-center justify-center font-black text-xs ${colors.badge} text-white shadow`}>
                          #{zone.response_priority_rank || zone.priority_rank}
                        </span>
                        <div>
                          <h3 className="font-bold text-sm text-white">{zone.zone_name}</h3>
                          <div className="text-[11px] text-slate-400">
                            Pop: {(zone.affected_population || zone.population || 0).toLocaleString()} • Active SOS: {zone.active_sos_count || 0}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className={`text-sm font-black ${colors.text}`}>
                          {Number(zone.risk_score != null ? zone.risk_score : 50).toFixed(1)}
                        </div>
                        <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded uppercase ${colors.badge} text-white`}>
                          {zone.risk_level}
                        </span>
                      </div>
                    </div>

                    {/* Risk Score Progress Bar */}
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2">
                      <div
                        className={`h-full ${colors.badge} transition-all duration-500`}
                        style={{ width: `${Math.min(Number(zone.risk_score || 0), 100)}%` }}
                      />
                    </div>


                    {/* AI Recommended Action & Trajectory */}
                    <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/60">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-slate-400">Trajectory:</span>
                        <span className="font-semibold text-slate-200 capitalize text-[11px]">
                          {zone.overall_trajectory || 'worsening'}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-amber-500/40 text-amber-300 font-bold text-[10px]">
                        {zone.recommended_action}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB CONTENT: MULTILINGUAL SOS FEED */}
          {activeTab === 'sos' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              
              {/* Language & Urgency Filter Chips */}
              <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 space-y-2">
                <div className="text-[10px] uppercase font-bold text-slate-400">Filter by Language</div>
                <div className="flex flex-wrap gap-1">
                  {['ALL', 'te', 'hi', 'en', 'ta', 'kn', 'ml'].map(lang => (
                    <button
                      key={lang}
                      onClick={() => setSosLangFilter(lang)}
                      className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
                        sosLangFilter === lang
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {lang === 'ALL' ? 'All Languages' : LANGUAGE_LABELS[lang] || lang.toUpperCase()}
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Urgency:</span>
                  <div className="flex gap-1">
                    {['ALL', 'critical', 'high', 'medium'].map(u => (
                      <button
                        key={u}
                        onClick={() => setSosUrgencyFilter(u)}
                        className={`px-2 py-0.5 rounded text-[10px] font-bold capitalize transition-all ${
                          sosUrgencyFilter === u
                            ? 'bg-amber-600 text-white'
                            : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                        }`}
                      >
                        {u}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* SOS Reports List */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                {filteredSOS.length === 0 ? (
                  <div className="text-center py-10 text-slate-500 text-xs">
                    No SOS reports matching current filters.
                  </div>
                ) : (
                  filteredSOS.map(sos => {
                    const ext = sos.structured_extraction || {};
                    const uCol = URGENCY_COLORS[sos.urgency] || URGENCY_COLORS.high;
                    const langCode = ext.detected_language || sos.language || 'en';

                    return (
                      <div key={sos.id} className="p-3 rounded-xl glass-card border border-slate-800 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="px-1.5 py-0.5 rounded bg-blue-900/60 border border-blue-700 text-blue-300 font-extrabold text-[10px] uppercase">
                              {LANGUAGE_LABELS[langCode] || langCode}
                              {ext.is_transliterated ? ' (Romanized)' : ''}
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold text-[10px] capitalize">
                              Need: {sos.need_type || 'Rescue'}
                            </span>
                          </div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${uCol.badge} text-white`}>
                            {sos.urgency}
                          </span>
                        </div>

                        {/* Citizen Message */}
                        <div className="p-2 rounded bg-slate-900/90 border border-slate-800 text-slate-200 text-xs italic">
                          "{sos.message}"
                        </div>

                        {/* Extraction Metadata */}
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <div>
                            Priority Score: <span className="font-bold text-red-400">{sos.priority_score || ext.priority_score || 50}/100</span>
                          </div>
                          <div>
                            People Affected: <span className="font-semibold text-white">{ext.people_count || '1+'}</span>
                          </div>
                        </div>

                        {/* Danger factor chips */}
                        {ext.danger_factors && ext.danger_factors.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/60">
                            {ext.danger_factors.map(factor => (
                              <span key={factor} className="px-1.5 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-900/80 text-[9px]">
                                ⚠️ {factor.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB CONTENT: ENVIRONMENTAL & DRONE TELEMETRY */}
          {activeTab === 'telemetry' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
              <div className="font-bold text-sm text-white border-b border-slate-800 pb-2">
                Hydrological & Aerial Sensor Grid
              </div>

              {/* River Gauges */}
              <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200 flex items-center gap-1.5">
                    <span>🌊</span> Krishna River Gauge (Prakasam Barrage)
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-red-600 text-white font-bold text-[10px]">
                    +1.75m Above Danger
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-slate-900">
                    <div className="text-slate-400">Current Gauge</div>
                    <div className="text-base font-black text-red-400">19.25 m</div>
                  </div>
                  <div className="p-2 rounded bg-slate-900">
                    <div className="text-slate-400">Danger Threshold</div>
                    <div className="text-base font-black text-amber-400">17.50 m</div>
                  </div>
                </div>
                <div className="text-[11px] text-slate-400">
                  Rate of Surge: <span className="font-bold text-red-400">+0.8 m/hr</span> (Rapid Inundation Risk)
                </div>
              </div>

              {/* Rainfall Intensity */}
              <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200 flex items-center gap-1.5">
                    <span>🌧️</span> Doppler Radar Rainfall Intensity
                  </span>
                  <span className="text-amber-400 font-bold">85 mm/hr</span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 w-[85%]"></div>
                </div>
                <div className="text-[11px] text-slate-400">
                  24h Cumulative Precipitation: <span className="text-white font-bold">210 mm</span> (Soil Saturated)
                </div>
              </div>

              {/* Drone Road Obstacle Overview */}
              <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200 flex items-center gap-1.5">
                    <span>🚁</span> Aerial Drone Obstacle Telemetry
                  </span>
                  <span className="text-sky-400 font-bold">{droneReadings.length} Reports</span>
                </div>
                <div className="space-y-1.5">
                  {droneReadings.slice(0, 4).map((d, i) => (
                    <div key={i} className="p-2 rounded bg-slate-900 text-[11px] flex items-center justify-between">
                      <span className="capitalize text-slate-300">{(d.obstacle_type || 'obstacle').replace('_', ' ')}</span>
                      <span className="text-amber-400 font-semibold">{d.water_depth != null ? d.water_depth : 0}m depth</span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${d.road_status === 'blocked' ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white'}`}>
                        {d.road_status || 'Survey'}
                      </span>
                    </div>
                  ))}

                </div>
              </div>
            </div>
          )}

          {/* TAB CONTENT: PHASE 7 – EVACUATION & DRONE INTELLIGENCE */}
          {activeTab === 'routes' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-4">

              {/* Action Bar: Route Recalculation & Quick Summary */}
              <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <span>🧠</span> AI Safe Pathfinding Engine
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Dynamically routes around drone-reported flooded roads & high-risk floodways
                    </p>
                  </div>
                  <button
                    onClick={handleRecalculateRoutes}
                    disabled={isRecalculatingRoutes}
                    className="px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all disabled:opacity-50"
                    title="Triggers live Dijkstra graph re-weighting with aerial drone obstacle telemetry"
                  >
                    <span className={isRecalculatingRoutes ? 'animate-spin' : ''}>🔄</span>
                    {isRecalculatingRoutes ? 'Computing...' : 'Recalculate Routes'}
                  </button>
                </div>
                <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/80 text-slate-300">
                  <span>Active Corridors: <strong className="text-emerald-400">{evacuationRoutes.length} sectors</strong></span>
                  <span>Drone Obstacles Bypassed: <strong className="text-amber-400">{droneReadings.filter(d => d.road_status === 'blocked').length} blocked</strong></span>
                </div>
              </div>

              {/* Nearest Safe Shelters Overview */}
              <div>
                <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5 mb-2">
                  <span>⛺</span> Nearest Safe Relief Shelters (High-Ground Havens)
                </div>
                <div className="space-y-1.5">
                  {[
                    { id: 'S_TADEPALLI', name: 'Tadepalli Primary Relief Haven', cap: 15000, occ: 4200, elev: 28.5, med: true, floodImmune: '100% Ridge Elevated' },
                    { id: 'S_KANAKADURGA', name: 'Kanakadurga High-Ground Center', cap: 8000, occ: 2800, elev: 34.0, med: true, floodImmune: 'Hillside Sanctuary' },
                    { id: 'S_AUTONAGAR_HIGH', name: 'Autonagar Industrial Elevated Shelter', cap: 6500, occ: 1900, elev: 26.0, med: false, floodImmune: 'Elevated Platform' },
                  ].map((s, i) => {
                    const occPct = Math.round((s.occ / s.cap) * 100);
                    return (
                      <div key={i} className="glass-card p-2.5 rounded-xl border border-slate-800 text-[11px] space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs">{s.name}</span>
                          <span className="px-1.5 py-0.5 text-[9px] font-bold rounded uppercase bg-emerald-900/80 text-emerald-300 border border-emerald-700/60">
                            OPEN ({s.floodImmune})
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-slate-400">
                          <span>Capacity: <strong className="text-white">{s.cap.toLocaleString()}</strong></span>
                          <span>Occupancy: <strong className="text-amber-300">{s.occ.toLocaleString()} ({occPct}%)</strong></span>
                          <span>Elev: <strong className="text-sky-300">{s.elev}m ASL</strong></span>
                          <span className={s.med ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
                            {s.med ? '🏥 Hospital' : '—'}
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                          <div
                            className={`h-full ${occPct > 80 ? 'bg-red-500' : occPct > 50 ? 'bg-amber-500' : 'bg-emerald-500'} transition-all`}
                            style={{ width: `${occPct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Evacuation Corridors (Recommended & Alternative) */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <span>🛣️</span> Sector Evacuation Corridors ({evacuationRoutes.length})
                  </span>
                  <span className="text-[10px] text-slate-400">Green = Recommended • Amber = Alternative</span>
                </div>

                {evacuationRoutes.length === 0 ? (
                  <div className="text-xs text-slate-500 text-center py-4 glass-card rounded-xl">
                    No active evacuation routes. Click "Seed Demo" or "Recalculate Routes" to generate.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {evacuationRoutes.map((route, idx) => {
                      const safetyColor = route.safety_score >= 80 ? 'text-emerald-400' : route.safety_score >= 60 ? 'text-amber-400' : 'text-red-400';
                      const riskBadgeBg = route.route_risk_level === 'HIGH' ? 'bg-red-600 text-white' : route.route_risk_level === 'MODERATE' ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white';

                      return (
                        <div key={route.route_id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2.5">
                          
                          {/* Route Origin & Actions */}
                          <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-2">
                            <div>
                              <div className="text-xs font-extrabold text-white flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                                {route.origin_name}
                              </div>
                              <div className="text-[11px] text-slate-400 mt-0.5">
                                Nearest Safe Haven: <span className="font-semibold text-emerald-300">{route.destination_name}</span>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className={`px-2 py-0.5 text-[9px] font-black rounded uppercase ${riskBadgeBg}`}>
                                {route.route_risk_level || 'LOW'} RISK
                              </span>
                              <button
                                onClick={() => {
                                  if (route.waypoints && route.waypoints[0] && leafletMapRef.current) {
                                    leafletMapRef.current.flyTo(route.waypoints[0], 14, { duration: 1.0 });
                                  }
                                }}
                                className="text-[10px] text-sky-400 hover:text-sky-300 underline flex items-center gap-0.5"
                              >
                                <span>📍</span> Focus Map
                              </button>
                            </div>
                          </div>

                          {/* RECOMMENDED ROUTE CARD */}
                          <div className="bg-emerald-950/30 border border-emerald-800/50 rounded-lg p-2 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                                <span>⭐</span> Recommended Safe Route
                              </span>
                              <span className="text-[10px] text-emerald-300 font-semibold">{route.distance_km} km • {route.estimated_time_minutes} min ETA</span>
                            </div>
                            <div className="grid grid-cols-3 gap-1 text-[10px]">
                              <div className="bg-slate-900/80 rounded p-1 text-center">
                                <div className="text-slate-400 text-[9px]">Distance</div>
                                <div className="font-bold text-white">{route.distance_km} km</div>
                              </div>
                              <div className="bg-slate-900/80 rounded p-1 text-center">
                                <div className="text-slate-400 text-[9px]">Travel Time</div>
                                <div className="font-bold text-amber-400">{route.estimated_time_minutes} min</div>
                              </div>
                              <div className="bg-slate-900/80 rounded p-1 text-center">
                                <div className="text-slate-400 text-[9px]">Safety Index</div>
                                <div className={`font-bold ${safetyColor}`}>{route.safety_score}/100</div>
                              </div>
                            </div>
                            {route.hazards_avoided && route.hazards_avoided.length > 0 && (
                              <div className="text-[10px] text-amber-300 flex items-center gap-1 pt-0.5">
                                <span>⚠️</span> {route.hazards_avoided.length} drone-detected road obstacle(s) bypassed safely
                              </div>
                            )}
                            {route.corridor_notes && route.corridor_notes.length > 0 && (
                              <div className="text-[10px] text-slate-300 italic">
                                ℹ️ {route.corridor_notes[0]}
                              </div>
                            )}
                          </div>

                          {/* ALTERNATIVE ROUTE CARD (if available) */}
                          {route.alternative_route && (
                            <div className="bg-amber-950/20 border border-amber-800/40 rounded-lg p-2 space-y-1.5">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1">
                                  <span>🔀</span> Alternative Backup Route
                                </span>
                                <span className="text-[10px] text-amber-300 font-semibold">
                                  {route.alternative_route.distance_km} km • {route.alternative_route.estimated_time_minutes} min ETA
                                </span>
                              </div>
                              <div className="text-[10px] text-slate-300">
                                Backup Shelter: <span className="font-semibold text-amber-200">{route.alternative_route.destination_name}</span>
                              </div>
                              <div className="grid grid-cols-2 gap-1 text-[10px]">
                                <div className="bg-slate-900/80 rounded p-1 text-center">
                                  <span className="text-slate-400 text-[9px]">Backup Distance: </span>
                                  <strong className="text-white">{route.alternative_route.distance_km} km</strong>
                                </div>
                                <div className="bg-slate-900/80 rounded p-1 text-center">
                                  <span className="text-slate-400 text-[9px]">Safety Index: </span>
                                  <strong className="text-amber-400">{route.alternative_route.safety_score}/100</strong>
                                </div>
                              </div>
                              <div className="text-[9px] text-slate-400 italic">
                                ℹ️ Standby path if primary corridor experiences unexpected surge or congestion.
                              </div>
                            </div>
                          )}

                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Drone Fleet Status & Aerial Intelligence */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
                    <span>🚁</span> Drone Fleet & Aerial Intelligence
                  </span>
                  <span className="text-[10px] text-sky-300 font-bold">2 Units Active</span>
                </div>

                {/* Drone Units Fleet Status Cards */}
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="glass-card p-2.5 rounded-xl border border-sky-800/60 text-[10px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs">Garuda-01</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Online"></span>
                    </div>
                    <div className="text-sky-300 font-semibold">Quad-Rotor LiDAR</div>
                    <div className="text-slate-400">Base: Tadepalli Hub (Z7)</div>
                    <div className="text-emerald-400 font-bold text-[9px] uppercase">● ACTIVE / SURVEYING</div>
                  </div>
                  <div className="glass-card p-2.5 rounded-xl border border-violet-800/60 text-[10px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs">Pushpak-02</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Online"></span>
                    </div>
                    <div className="text-violet-300 font-semibold">Fixed-Wing Multispectral</div>
                    <div className="text-slate-400">Base: Gunadala Post (Z6)</div>
                    <div className="text-emerald-400 font-bold text-[9px] uppercase">● ACTIVE / PATROL</div>
                  </div>
                </div>

                {/* Drone Recon Missions */}
                {droneReconMissions.length > 0 && (
                  <div className="space-y-2">
                    {droneReconMissions.map((mission, idx) => {
                      const missionColors = ['text-cyan-400', 'text-violet-400'];
                      const missionBorderColors = ['border-cyan-800', 'border-violet-800'];
                      const c = missionColors[idx % missionColors.length];
                      const b = missionBorderColors[idx % missionBorderColors.length];
                      return (
                        <div key={mission.mission_id} className={`glass-card p-3 rounded-xl border ${b} space-y-1.5`}>
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className={`text-xs font-bold ${c}`}>{mission.mission_id}</div>
                              <div className="text-[10px] text-slate-300">{mission.drone_callsign}</div>
                            </div>
                            <span className="text-[10px] text-slate-400 font-semibold">{mission.estimated_flight_minutes} min flight</span>
                          </div>
                          <div className="text-[10px] text-slate-300">{mission.mission_objective}</div>
                          <div className="grid grid-cols-2 gap-1 text-[10px]">
                            <div className="bg-slate-900 rounded p-1 text-center">
                              <div className="text-slate-400 text-[9px]">Flight Distance</div>
                              <div className="font-bold text-white">{mission.total_distance_km} km</div>
                            </div>
                            <div className="bg-slate-900 rounded p-1 text-center">
                              <div className="text-slate-400 text-[9px]">Waypoints</div>
                              <div className="font-bold text-white">{mission.waypoints ? mission.waypoints.length : 0} waypoints</div>
                            </div>
                          </div>
                          {mission.priority_targets && mission.priority_targets.length > 0 && (
                            <div className="space-y-0.5 pt-1">
                              <div className="text-[9px] uppercase font-bold text-slate-400">Priority Targets:</div>
                              {mission.priority_targets.map((t, i) => (
                                <div key={i} className="text-[10px] text-slate-300 flex items-center gap-1">
                                  <span className="text-sky-400">▸</span> {t}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

            </div>
          )}


          {/* TAB CONTENT: PHASE 8 – POST-DISASTER RELIEF & RECOVERY */}
          {activeTab === 'relief' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3.5">
              
              {/* Header Action Bar */}
              <div className="glass-card p-3 rounded-xl border border-emerald-800/60 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <span>🏥</span> Post-Disaster Relief & Recovery Command
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Damage assessment, multi-sector relief dispatch, and infrastructure restoration
                    </p>
                  </div>
                  <button
                    onClick={() => setShowNewRequestModal(true)}
                    className="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1 shadow-md shadow-emerald-600/30 transition-all"
                    title="Submit a citizen or field worker relief supply request"
                  >
                    <span>+</span> New Request
                  </button>
                </div>

                {/* Sub-Navigation Pills */}
                <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/80">
                  {[
                    { id: 'overview', label: '📊 Overview' },
                    { id: 'community', label: '🤝 Community Aid' },
                    { id: 'damage', label: `📑 Damage (${damageAssessments.length})` },
                    { id: 'camps', label: `⛺ Camps (${reliefCamps.length})` },
                    { id: 'requests', label: `📦 Requests (${reliefRequests.length})` },
                    { id: 'resources', label: `💊 Resources (${reliefResources.length})` },
                    { id: 'teams', label: `🚒 Teams (${reliefTeams.length})` },
                    { id: 'recovery', label: `🏗️ Recovery (${recoveryItems.length})` },
                    { id: 'fundraising', label: `💰 Fund (${reliefFund ? '₹' + (reliefFund.raised_amount/100000).toFixed(1) + 'L' : '💰 Fund'})` },
                  ].map(sub => (
                    <button
                      key={sub.id}
                      onClick={() => setReliefSubTab(sub.id)}
                      className={`px-2 py-1 rounded text-[10px] font-bold transition-all ${
                        reliefSubTab === sub.id
                          ? 'bg-emerald-700 text-white shadow'
                          : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      }`}
                    >
                      {sub.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 1. SUB-TAB: OVERVIEW & KPIS */}
              {reliefSubTab === 'overview' && (
                <div className="space-y-3">
                  {/* KPI Grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="glass-card p-2.5 rounded-xl border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Total Affected People</div>
                      <div className="text-lg font-black text-white mt-0.5">
                        {reliefSummary ? reliefSummary.total_affected_people.toLocaleString() : '122,400'}
                      </div>
                      <div className="text-[10px] text-red-400 font-semibold mt-0.5">
                        {reliefSummary ? reliefSummary.total_injured_count : 185} injured • {reliefSummary ? reliefSummary.total_missing_count : 24} missing
                      </div>
                    </div>
                    <div className="glass-card p-2.5 rounded-xl border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Relief Camp Capacity</div>
                      <div className="text-lg font-black text-emerald-400 mt-0.5">
                        {reliefSummary ? reliefSummary.total_camp_occupancy.toLocaleString() : '13,100'}
                        <span className="text-xs text-slate-400 font-normal"> / {reliefSummary ? reliefSummary.total_camp_capacity.toLocaleString() : '35,000'}</span>
                      </div>
                      <div className="text-[10px] text-emerald-300 font-semibold mt-0.5">
                        {reliefSummary ? reliefSummary.camp_occupancy_pct : 37.4}% Occupied ({reliefSummary ? reliefSummary.available_beds_total : 21900} beds free)
                      </div>
                    </div>
                    <div className="glass-card p-2.5 rounded-xl border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Active Relief Teams</div>
                      <div className="text-lg font-black text-blue-400 mt-0.5">
                        {reliefSummary ? reliefSummary.active_teams_count : 6} Teams
                      </div>
                      <div className="text-[10px] text-slate-300 mt-0.5">
                        {reliefSummary ? reliefSummary.total_team_personnel : 70} personnel deployed
                      </div>
                    </div>
                    <div className="glass-card p-2.5 rounded-xl border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Overall Recovery Progress</div>
                      <div className="text-lg font-black text-amber-400 mt-0.5">
                        {reliefSummary ? reliefSummary.overall_recovery_progress_pct : 43.1}%
                      </div>
                      <div className="text-[10px] text-amber-300 font-semibold mt-0.5">
                        {reliefSummary ? reliefSummary.restored_items_count : 1} restored • {reliefSummary ? reliefSummary.under_repair_items_count : 6} underway
                      </div>
                    </div>
                  </div>

                  {/* Pending Relief Demands Alert Card */}
                  <div className="glass-card p-3 rounded-xl border border-amber-800/60 bg-amber-950/20 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-300 text-xs flex items-center gap-1.5">
                        <span>⚠️</span> Outstanding Relief Requests
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-600 text-white">
                        {reliefSummary ? reliefSummary.pending_requests_count : 4} Pending
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300">
                      {reliefSummary ? reliefSummary.critical_requests_count : 3} requests flagged with <strong>CRITICAL</strong> urgency requiring immediate air/boat delivery.
                    </p>
                  </div>

                  {/* Quick Summary of Camps */}
                  <div className="space-y-1.5">
                    <div className="text-xs font-bold text-slate-300 flex items-center justify-between">
                      <span>⛺ Designated Relief Camps</span>
                      <button onClick={() => setReliefSubTab('camps')} className="text-emerald-400 text-[10px] underline">View All</button>
                    </div>
                    {reliefCamps.slice(0, 3).map(c => {
                      const occ = Math.round((c.current_occupancy / floatSafe(c.capacity)) * 100);
                      return (
                        <div key={c.id} className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-[11px] space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white">{c.name}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${c.status === 'Full' ? 'bg-red-600 text-white' : c.status === 'Near Capacity' ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white'}`}>
                              {c.status} ({occ}%)
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-slate-400 text-[10px]">
                            <span>Occupancy: {c.current_occupancy} / {c.capacity}</span>
                            <span>Beds Free: <strong className="text-emerald-400">{c.available_beds}</strong></span>
                            <span>{c.medical_facility ? '🏥 Med Clinic' : 'No Clinic'}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 2. SUB-TAB: DAMAGE & NEEDS ASSESSMENT */}
              {reliefSubTab === 'damage' && (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Sectors ranked by Post-Disaster Priority Score</span>
                    <span className="text-emerald-400 font-bold">{damageAssessments.length} Zones Assessed</span>
                  </div>

                  {damageAssessments.map(d => {
                    const sevBadge = d.damage_severity === 'CRITICAL' ? 'bg-red-600' : d.damage_severity === 'HIGH' ? 'bg-orange-600' : d.damage_severity === 'MEDIUM' ? 'bg-yellow-600 text-slate-900' : 'bg-emerald-600';
                    const prioBadge = d.priority_level === 'CRITICAL' ? 'border-red-500 text-red-400' : d.priority_level === 'HIGH' ? 'border-orange-500 text-orange-400' : 'border-yellow-500 text-yellow-400';

                    return (
                      <div key={d.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                        <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-1.5">
                          <div>
                            <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full bg-red-400"></span>
                              {d.zone_name}
                            </div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              Status: <span className="font-semibold text-sky-300">{d.assessment_status}</span> • Evaluated: {d.assessed_by || 'NDRF Survey Team'}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${sevBadge} text-white`}>
                              {d.damage_severity} DAMAGE
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${prioBadge} bg-slate-900`}>
                              Priority {d.priority_score}/100
                            </span>
                          </div>
                        </div>

                        {/* Physical Damage & Human Impact */}
                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                          <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 space-y-1">
                            <div className="text-[10px] uppercase font-bold text-slate-400">Physical Damage</div>
                            <div className="text-slate-300">Buildings: <strong className="text-red-400">{d.buildings_damaged.toLocaleString()}</strong> ({d.buildings_destroyed} collapsed)</div>
                            <div className="text-slate-300">Roads: <strong className="text-amber-400">{d.roads_damaged_km} km</strong> disrupted</div>
                            <div className="text-slate-300">Bridges Disrupted: <strong className="text-amber-400">{d.bridges_damaged}</strong></div>
                          </div>
                          <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 space-y-1">
                            <div className="text-[10px] uppercase font-bold text-slate-400">Human Impact</div>
                            <div className="text-slate-300">Affected: <strong className="text-white">{d.affected_people.toLocaleString()}</strong></div>
                            <div className="text-slate-300">Injured: <strong className="text-red-400">{d.injured_count}</strong> • Missing: <strong className="text-red-500">{d.missing_count}</strong></div>
                            <div className="text-slate-300">Rescued: <strong className="text-emerald-400">{d.rescued_count.toLocaleString()}</strong></div>
                          </div>
                        </div>

                        {/* Immediate Relief Needs */}
                        <div className="p-2 rounded bg-emerald-950/20 border border-emerald-800/40 text-[10px] space-y-1">
                          <div className="font-bold text-emerald-400 uppercase tracking-wider">Required Relief Supplies</div>
                          <div className="grid grid-cols-3 gap-1 text-slate-300">
                            <div>🍲 Food Packets: <strong>{d.food_packets_needed.toLocaleString()}</strong></div>
                            <div>💧 Water Liters: <strong>{d.water_liters_needed.toLocaleString()}L</strong></div>
                            <div>💊 Medical Kits: <strong>{d.medical_kits_needed}</strong></div>
                            <div>⛺ Temp Tents: <strong>{d.temporary_shelters_needed}</strong></div>
                            <div>🛌 Blankets: <strong>{d.blankets_needed.toLocaleString()}</strong></div>
                            <div>👥 Displaced: <strong>{d.displaced_people.toLocaleString()}</strong></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 3. SUB-TAB: RELIEF CAMPS */}
              {reliefSubTab === 'camps' && (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Designated Evacuation & Relief Camps</span>
                    <span className="text-emerald-400 font-bold">{reliefCamps.length} Facilities Active</span>
                  </div>

                  {reliefCamps.map(camp => {
                    const occ = Math.round((camp.current_occupancy / floatSafe(camp.capacity)) * 100);
                    const statusBg = camp.status === 'Full' ? 'bg-red-600' : camp.status === 'Near Capacity' ? 'bg-amber-600' : 'bg-emerald-600';

                    return (
                      <div key={camp.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                        <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-1.5">
                          <div>
                            <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                              <span>⛺</span> {camp.name}
                            </div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              {camp.location_name} • Officer: {camp.contact_person || 'Field In-Charge'} ({camp.contact_phone || 'Govt Line'})
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${statusBg} text-white`}>
                              {camp.status}
                            </span>
                            <button
                              onClick={() => {
                                if (leafletMapRef.current && camp.latitude && camp.longitude) {
                                  leafletMapRef.current.flyTo([camp.latitude, camp.longitude], 15, { duration: 1.0 });
                                }
                              }}
                              className="text-[10px] text-sky-400 hover:text-sky-300 underline ml-1"
                            >
                              Map
                            </button>
                          </div>
                        </div>

                        {/* Capacity / Occupancy Bar */}
                        <div>
                          <div className="flex items-center justify-between text-[11px] mb-1 text-slate-300">
                            <span>Occupancy: <strong>{camp.current_occupancy.toLocaleString()} / {camp.capacity.toLocaleString()}</strong></span>
                            <span>{occ}% Full ({camp.available_beds} beds available)</span>
                          </div>
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${occ >= 95 ? 'bg-red-500' : occ >= 75 ? 'bg-amber-500' : 'bg-emerald-500'} transition-all`}
                              style={{ width: `${Math.min(occ, 100)}%` }}
                            />
                          </div>
                        </div>

                        {/* Supplies & Health Amenities */}
                        <div className="grid grid-cols-3 gap-1 text-[10px] bg-slate-900/80 p-2 rounded border border-slate-800">
                          <div>
                            <span className="text-slate-400">Medical Unit:</span>
                            <div className={`font-bold ${camp.medical_facility ? 'text-emerald-400' : 'text-slate-500'}`}>
                              {camp.medical_facility ? '🏥 On-Site Doctors' : 'None'}
                            </div>
                          </div>
                          <div>
                            <span className="text-slate-400">Food Supplies:</span>
                            <div className={`font-bold ${camp.food_supply_status === 'Adequate' ? 'text-emerald-400' : 'text-amber-400'}`}>
                              🍲 {camp.food_supply_status || 'Adequate'}
                            </div>
                          </div>
                          <div>
                            <span className="text-slate-400">Clean Water:</span>
                            <div className={`font-bold ${camp.water_supply_status === 'Adequate' ? 'text-emerald-400' : 'text-amber-400'}`}>
                              💧 {camp.water_supply_status || 'Adequate'}
                            </div>
                          </div>
                        </div>

                        {/* Quick Occupancy Adjustment Buttons */}
                        <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                          <span className="text-slate-400">Update Intake:</span>
                          <button
                            disabled={isUpdatingStatus}
                            onClick={async () => {
                              try {
                                setIsUpdatingStatus(true);
                                const newOcc = Math.max(0, camp.current_occupancy + 100);
                                await fetch(`${API_BASE}/relief/camps/${camp.id}`, {
                                  method: 'PUT',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ current_occupancy: newOcc })
                                });
                              } finally {
                                setIsUpdatingStatus(false);
                              }
                            }}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-50"
                          >
                            +100 Intake
                          </button>
                          <button
                            disabled={isUpdatingStatus || camp.current_occupancy <= 0}
                            onClick={async () => {
                              try {
                                setIsUpdatingStatus(true);
                                const newOcc = Math.max(0, camp.current_occupancy - 100);
                                await fetch(`${API_BASE}/relief/camps/${camp.id}`, {
                                  method: 'PUT',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ current_occupancy: newOcc })
                                });
                              } finally {
                                setIsUpdatingStatus(false);
                              }
                            }}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-50"
                          >
                            -100 Discharged
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 4. SUB-TAB: RELIEF REQUESTS FEED */}
              {reliefSubTab === 'requests' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Ranked by Transparent Priority Score</span>
                    <button
                      onClick={() => setShowNewRequestModal(true)}
                      className="text-emerald-400 font-bold hover:underline"
                    >
                      + Create Request
                    </button>
                  </div>

                  {reliefRequests.map(req => {
                    const prioColor = req.priority === 'Critical' ? 'bg-red-600 text-white' : req.priority === 'High' ? 'bg-orange-600 text-white' : 'bg-amber-600 text-white';
                    const statusColor = req.status === 'Fulfilled' ? 'bg-emerald-600 text-white' : req.status === 'Dispatched' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-amber-300 border border-amber-600/50';

                    return (
                      <div key={req.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                        <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-1.5">
                          <div>
                            <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                              <span className="font-mono text-emerald-400">{req.request_code}</span>
                              <span className="text-slate-300">• {req.category}</span>
                            </div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              Location: <span className="font-semibold text-slate-200">{req.location_name}</span> ({req.people_count} individuals)
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${prioColor}`}>
                              {req.priority}
                            </span>
                            <span className="text-[10px] font-mono text-red-400 font-bold">
                              Priority: {req.priority_score}/100
                            </span>
                          </div>
                        </div>

                        <p className="text-slate-300 text-[11px] bg-slate-900/90 p-2 rounded border border-slate-800 italic">
                          "{req.description}"
                        </p>

                        <div className="flex items-center justify-between text-[10px] text-slate-400">
                          <span>Requester: <strong className="text-slate-200">{req.requester_name || 'Citizen'}</strong> ({req.contact_phone || 'Emergency'})</span>
                          <span className={`px-2 py-0.5 rounded font-bold uppercase ${statusColor}`}>
                            {req.status}
                          </span>
                        </div>

                        {/* Quick Status Dispatch Actions */}
                        <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                          <span className="text-slate-400">Change Status:</span>
                          {req.status !== 'Dispatched' && (
                            <button
                              disabled={isUpdatingStatus}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  await fetch(`${API_BASE}/relief/requests/${req.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ status: 'Dispatched', assigned_team: 'NDRF Rescue Unit 01' })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-blue-900/80 hover:bg-blue-800 text-blue-200 border border-blue-700 disabled:opacity-50"
                            >
                              Dispatch Team
                            </button>
                          )}
                          {req.status !== 'Fulfilled' && (
                            <button
                              disabled={isUpdatingStatus}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  await fetch(`${API_BASE}/relief/requests/${req.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ status: 'Fulfilled' })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 disabled:opacity-50"
                            >
                              Mark Fulfilled
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 5. SUB-TAB: RESOURCE INVENTORY */}
              {reliefSubTab === 'resources' && (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Emergency Relief Supply Depot Inventory</span>
                    <span className="text-emerald-400 font-bold">{reliefResources.length} Stock Categories</span>
                  </div>

                  <div className="space-y-2">
                    {reliefResources.map(res => {
                      const availPct = Math.round((res.available_qty / floatSafe(res.required_qty)) * 100);
                      const isLow = res.low_stock_warning || (res.available_qty <= res.low_stock_threshold);

                      return (
                        <div key={res.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                          <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                            <div>
                              <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                                <span>📦</span> {res.item_name}
                              </div>
                              <span className="text-[10px] text-slate-400 uppercase font-semibold">{res.category}</span>
                            </div>
                            {isLow ? (
                              <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-red-600 text-white animate-pulse">
                                Low Stock Alert
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-emerald-700 text-emerald-100">
                                Adequate
                              </span>
                            )}
                          </div>

                          <div className="grid grid-cols-4 gap-1 text-[10px] text-center">
                            <div className="bg-slate-900/90 p-1.5 rounded">
                              <div className="text-slate-400">Available</div>
                              <div className="font-bold text-emerald-400 text-xs">{res.available_qty.toLocaleString()} {res.unit}</div>
                            </div>
                            <div className="bg-slate-900/90 p-1.5 rounded">
                              <div className="text-slate-400">Required</div>
                              <div className="font-bold text-white text-xs">{res.required_qty.toLocaleString()} {res.unit}</div>
                            </div>
                            <div className="bg-slate-900/90 p-1.5 rounded">
                              <div className="text-slate-400">Distributed</div>
                              <div className="font-bold text-sky-400 text-xs">{res.distributed_qty.toLocaleString()} {res.unit}</div>
                            </div>
                            <div className="bg-slate-900/90 p-1.5 rounded">
                              <div className="text-slate-400">Remaining</div>
                              <div className="font-bold text-amber-300 text-xs">{res.remaining_qty.toLocaleString()} {res.unit}</div>
                            </div>
                          </div>

                          {/* Stock vs Requirement Progress Bar */}
                          <div>
                            <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
                              <span>Supply Coverage:</span>
                              <span>{availPct}% of emergency need</span>
                            </div>
                            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${isLow ? 'bg-red-500' : 'bg-emerald-500'} transition-all`}
                                style={{ width: `${Math.min(availPct, 100)}%` }}
                              />
                            </div>
                          </div>

                          {/* Fast Dispense / Restock Buttons */}
                          <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                            <span className="text-slate-400">Stock Action:</span>
                            <button
                              disabled={isUpdatingStatus}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  const amt = res.category === 'Medical' ? 50 : 500;
                                  await fetch(`${API_BASE}/relief/resources/${res.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ available_qty: res.available_qty + amt })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 disabled:opacity-50"
                            >
                              + Replenish
                            </button>
                            <button
                              disabled={isUpdatingStatus || res.available_qty <= 0}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  const amt = res.category === 'Medical' ? 50 : 500;
                                  await fetch(`${API_BASE}/relief/resources/${res.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      available_qty: Math.max(0, res.available_qty - amt),
                                      distributed_qty: res.distributed_qty + amt
                                    })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-sky-900/80 hover:bg-sky-800 text-sky-200 border border-sky-700 disabled:opacity-50"
                            >
                              - Distribute
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 6. SUB-TAB: RELIEF TEAMS */}
              {reliefSubTab === 'teams' && (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Deployed Humanitarian & Rescue Teams</span>
                    <span className="text-blue-400 font-bold">{reliefTeams.length} Units Active</span>
                  </div>

                  <div className="space-y-2">
                    {reliefTeams.map(team => {
                      const statusColor = team.status === 'Deployed' ? 'bg-blue-600 text-white' : team.status === 'En Route' ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white';

                      return (
                        <div key={team.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                          <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-1.5">
                            <div>
                              <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                                <span>🚒</span> {team.name}
                              </div>
                              <div className="text-[10px] text-slate-400 mt-0.5">
                                Type: <strong className="text-slate-200 capitalize">{team.team_type}</strong> • Leader: {team.leader_name} ({team.contact_phone || 'Radio Ch. 4'})
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${statusColor}`}>
                                {team.status}
                              </span>
                              <button
                                onClick={() => {
                                  if (leafletMapRef.current && team.latitude && team.longitude) {
                                    leafletMapRef.current.flyTo([team.latitude, team.longitude], 15, { duration: 1.0 });
                                  }
                                }}
                                className="text-[10px] text-sky-400 hover:text-sky-300 underline ml-1"
                              >
                                Map
                              </button>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/80 p-2 rounded border border-slate-800">
                            <div>
                              <span className="text-slate-400">Team Strength:</span>
                              <div className="font-bold text-white">{team.members_count} personnel</div>
                            </div>
                            <div>
                              <span className="text-slate-400">Current Task:</span>
                              <div className="font-semibold text-sky-300">{team.assigned_task || 'Patrol & Assessment'}</div>
                            </div>
                          </div>

                          {/* Quick Team Status Toggle */}
                          <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                            <span className="text-slate-400">Status:</span>
                            {['Deployed', 'En Route', 'Standby'].map(st => (
                              <button
                                key={st}
                                disabled={isUpdatingStatus || team.status === st}
                                onClick={async () => {
                                  try {
                                    setIsUpdatingStatus(true);
                                    await fetch(`${API_BASE}/relief/teams/${team.id}`, {
                                      method: 'PUT',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({ status: st })
                                    });
                                  } finally {
                                    setIsUpdatingStatus(false);
                                  }
                                }}
                                className={`px-2 py-0.5 rounded border text-[10px] transition-all ${
                                  team.status === st
                                    ? 'bg-blue-600 text-white border-blue-500 font-bold'
                                    : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                                }`}
                              >
                                {st}
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 7. SUB-TAB: INFRASTRUCTURE RECOVERY PROGRESS */}
              {reliefSubTab === 'recovery' && (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Critical Infrastructure Restoration Tracking</span>
                    <span className="text-amber-400 font-bold">{recoveryItems.length} Projects Monitored</span>
                  </div>

                  <div className="space-y-2">
                    {recoveryItems.map(item => {
                      const isRestored = item.progress_pct >= 100 || item.recovery_status === 'Restored';
                      const statusBadge = isRestored ? 'bg-emerald-600 text-white' : item.recovery_status === 'Under Repair' ? 'bg-amber-600 text-white' : 'bg-red-600 text-white';

                      return (
                        <div key={item.id} className="glass-card p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                          <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-1.5">
                            <div>
                              <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                                <span>🏗️</span> {item.name}
                              </div>
                              <div className="text-[10px] text-slate-400 mt-0.5">
                                Category: <strong className="text-slate-200 capitalize">{item.category}</strong> • Agency: {item.responsible_agency || 'Disaster Cell'}
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${statusBadge}`}>
                                {item.recovery_status} ({item.progress_pct}%)
                              </span>
                              <button
                                onClick={() => {
                                  if (leafletMapRef.current && item.latitude && item.longitude) {
                                    leafletMapRef.current.flyTo([item.latitude, item.longitude], 15, { duration: 1.0 });
                                  }
                                }}
                                className="text-[10px] text-sky-400 hover:text-sky-300 underline ml-1"
                              >
                                Map
                              </button>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div>
                            <div className="flex items-center justify-between text-[10px] text-slate-300 mb-1">
                              <span>Restoration: <strong>{item.progress_pct}%</strong></span>
                              <span>Target: <strong className="text-sky-300">{item.estimated_restoration || 'In progress'}</strong></span>
                            </div>
                            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${isRestored ? 'bg-emerald-500' : 'bg-amber-500'} transition-all duration-500`}
                                style={{ width: `${item.progress_pct}%` }}
                              />
                            </div>
                          </div>

                          {/* Quick Progress Increment Buttons */}
                          <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                            <span className="text-slate-400">Update Progress:</span>
                            <button
                              disabled={isUpdatingStatus || item.progress_pct >= 100}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  const newPct = Math.min(100, item.progress_pct + 15);
                                  await fetch(`${API_BASE}/relief/recovery/${item.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      progress_pct: newPct,
                                      recovery_status: newPct >= 100 ? 'Restored' : 'Under Repair'
                                    })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-50"
                            >
                              +15%
                            </button>
                            <button
                              disabled={isUpdatingStatus || item.progress_pct >= 100}
                              onClick={async () => {
                                try {
                                  setIsUpdatingStatus(true);
                                  await fetch(`${API_BASE}/relief/recovery/${item.id}`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      progress_pct: 100,
                                      recovery_status: 'Restored'
                                    })
                                  });
                                } finally {
                                  setIsUpdatingStatus(false);
                                }
                              }}
                              className="px-2 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 disabled:opacity-50"
                            >
                              Mark 100% Restored
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {reliefSubTab === 'fundraising' && (
                <div className="space-y-3">
                  {/* Campaign Header / Progress Card */}
                  <div className="glass-card p-3.5 rounded-xl border border-amber-500/40 bg-slate-900/90 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] uppercase tracking-wider font-extrabold text-amber-400">
                          Official Disaster Relief Campaign
                        </span>
                        <h3 className="font-extrabold text-white text-sm mt-0.5">
                          {reliefFund ? reliefFund.campaign_name : 'Kerala Flood Relief & Emergency Recovery Fund 2026'}
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          Verified Govt & NGO Relief Drive • Immediate Citizen Assistance & Infra Support
                        </p>
                      </div>
                      <button
                        onClick={() => setShowDonateModal(true)}
                        className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md shadow-amber-600/30 flex items-center gap-1 transition-all whitespace-nowrap"
                      >
                        <span>💰</span> Donate (Demo)
                      </button>
                    </div>

                    {/* Progress Bar & Stats */}
                    {reliefFund && (() => {
                      const pct = reliefFund.funding_progress_pct ?? reliefFund.progress_pct ?? 0;
                      const donors = reliefFund.donor_count ?? reliefFund.total_donors ?? 0;
                      return (
                        <div className="space-y-1.5 pt-1 border-t border-slate-800/80">
                          <div className="flex justify-between items-baseline text-xs">
                            <div className="font-mono">
                              <span className="text-slate-400 text-[10px]">Raised: </span>
                              <span className="text-emerald-400 font-extrabold text-sm">₹{(reliefFund.raised_amount / 100000).toFixed(2)} Lakhs</span>
                              <span className="text-slate-500 text-[10px]"> / ₹{(reliefFund.target_amount / 10000000).toFixed(1)} Cr Goal</span>
                            </div>
                            <div className="text-amber-400 font-extrabold font-mono text-xs">
                              {pct}% Funded
                            </div>
                          </div>

                          {/* Visual Progress Bar */}
                          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
                            <div
                              className="h-full bg-gradient-to-r from-amber-500 via-emerald-500 to-emerald-400 rounded-full transition-all duration-700"
                              style={{ width: `${Math.min(100, pct)}%` }}
                            />
                          </div>

                          <div className="flex justify-between items-center text-[10px] text-slate-400 pt-0.5">
                            <span>👥 <strong>{donors.toLocaleString()}</strong> Verified Donors</span>
                            <span>🔒 Encrypted Mock Ledger</span>
                          </div>
                        </div>
                      );
                    })()}

                    {/* Allocation Buckets */}
                    <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px]">
                      <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-slate-400 block font-semibold">🍞 Food & Rations (30%)</span>
                        <span className="text-emerald-400 font-mono font-bold">₹{reliefFund ? ((reliefFund.raised_amount * 0.3) / 100000).toFixed(1) : 73.5}L Allocated</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-slate-400 block font-semibold">💊 Medical & Health (25%)</span>
                        <span className="text-emerald-400 font-mono font-bold">₹{reliefFund ? ((reliefFund.raised_amount * 0.25) / 100000).toFixed(1) : 61.2}L Allocated</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-slate-400 block font-semibold">⛺ Temp Shelters (25%)</span>
                        <span className="text-emerald-400 font-mono font-bold">₹{reliefFund ? ((reliefFund.raised_amount * 0.25) / 100000).toFixed(1) : 61.2}L Allocated</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-slate-400 block font-semibold">🏗️ Infra Rebuild (20%)</span>
                        <span className="text-emerald-400 font-mono font-bold">₹{reliefFund ? ((reliefFund.raised_amount * 0.20) / 100000).toFixed(1) : 49.0}L Allocated</span>
                      </div>
                    </div>
                  </div>

                  {/* Recent Donations Feed */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                      <span className="font-bold text-slate-300">Recent Transparent Contributions</span>
                      <span className="text-amber-400 font-mono">{reliefDonations.length} Live Records</span>
                    </div>

                    {reliefDonations.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800">
                        No transactions recorded yet. Click "Donate (Demo)" to simulate aid contribution!
                      </div>
                    ) : (
                      reliefDonations.map(don => (
                        <div key={don.id || don.reference_id} className="glass-card p-2.5 rounded-xl border border-slate-800 flex items-center justify-between gap-2 text-xs">
                          <div className="space-y-0.5">
                            <div className="font-extrabold text-white flex items-center gap-1.5">
                              <span>💳</span> {don.donor_name}
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-slate-800 text-amber-300 border border-slate-700">
                                {don.reference_id}
                              </span>
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Bucket: <strong className="text-sky-300">{don.category}</strong>
                              {don.message && <span className="text-slate-400 italic font-normal"> — "{don.message}"</span>}
                            </div>
                          </div>
                          <div className="text-right whitespace-nowrap">
                            <div className="font-extrabold text-emerald-400 font-mono text-sm">
                              +₹{don.amount ? don.amount.toLocaleString() : '0'}
                            </div>
                            <div className="text-[9px] text-slate-500">
                              {don.created_at ? new Date(don.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {reliefSubTab === 'community' && (() => {
                const communityTeams = reliefTeams.filter(t => 
                  t.team_type === 'Community Assistance' || t.name.includes('Volunteer') || t.name.includes('Civic') || t.team_type === 'Rescue'
                );
                const activeTeamsCount = communityTeams.filter(t => t.status === 'Available' || t.status === 'On Mission').length;
                const pendingRequests = reliefRequests.filter(r => r.status === 'Pending' || r.status === 'SUBMITTED');
                const assignedRequests = reliefRequests.filter(r => r.status === 'Assigned' || r.status === 'In Progress');
                const completedRequests = reliefRequests.filter(r => r.status === 'Completed' || r.status === 'Resolved');
                const peopleAssistedCount = completedRequests.reduce((sum, r) => sum + (r.people_count || 1), 0);

                const currentTeam = communityTeams.find(t => t.id === selectedCommunityTeamId) || communityTeams[0] || reliefTeams[0];

                return (
                  <div className="space-y-3.5">
                    
                    {/* 1. COMMUNITY ASSISTANCE SUMMARY KPI CARDS */}
                    <div className="grid grid-cols-4 gap-2">
                      <div className="glass-card p-2.5 rounded-xl border border-blue-500/40 bg-slate-900/90 text-center">
                        <span className="text-[10px] text-slate-400 font-bold uppercase block">Active Teams</span>
                        <span className="text-base font-extrabold text-blue-400 font-mono">{activeTeamsCount}</span>
                        <span className="text-[9px] text-slate-500 block">Volunteer Units</span>
                      </div>
                      <div className="glass-card p-2.5 rounded-xl border border-amber-500/40 bg-slate-900/90 text-center">
                        <span className="text-[10px] text-slate-400 font-bold uppercase block">Pending Help</span>
                        <span className="text-base font-extrabold text-amber-400 font-mono">{pendingRequests.length}</span>
                        <span className="text-[9px] text-slate-500 block">Needs Assignment</span>
                      </div>
                      <div className="glass-card p-2.5 rounded-xl border border-purple-500/40 bg-slate-900/90 text-center">
                        <span className="text-[10px] text-slate-400 font-bold uppercase block">Assigned Requests</span>
                        <span className="text-base font-extrabold text-purple-400 font-mono">{assignedRequests.length}</span>
                        <span className="text-[9px] text-slate-500 block">Active Missions</span>
                      </div>
                      <div className="glass-card p-2.5 rounded-xl border border-emerald-500/40 bg-slate-900/90 text-center">
                        <span className="text-[10px] text-slate-400 font-bold uppercase block">People Assisted</span>
                        <span className="text-base font-extrabold text-emerald-400 font-mono">{peopleAssistedCount + 145}</span>
                        <span className="text-[9px] text-slate-500 block">Lives Impacted</span>
                      </div>
                    </div>

                    {/* 2. TEAM SELECTOR & LOCATION SAFETY CHECKER */}
                    <div className="glass-card p-3 rounded-xl border border-slate-700 bg-slate-900/80 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-extrabold text-white flex items-center gap-1.5">
                          <span>🤝</span> Select Active Community Volunteer Unit:
                        </span>
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          🟢 Safe High-Ground Platform Verified
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        {communityTeams.slice(0, 3).map(team => {
                          const isSelected = currentTeam && currentTeam.id === team.id;
                          return (
                            <button
                              key={team.id}
                              onClick={() => setSelectedCommunityTeamId(team.id)}
                              className={`p-2 rounded-lg border text-left transition-all ${
                                isSelected
                                  ? 'bg-blue-950/80 border-blue-500 text-white shadow-md'
                                  : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:bg-slate-800'
                              }`}
                            >
                              <div className="font-bold text-xs flex items-center justify-between">
                                <span className="truncate">{team.name}</span>
                                <span className={`px-1.5 py-0.2 rounded text-[8px] uppercase font-black shrink-0 ${
                                  team.status === 'Available' ? 'bg-emerald-600 text-white' : 'bg-purple-600 text-white'
                                }`}>
                                  {team.status}
                                </span>
                              </div>
                              <div className="text-[10px] text-slate-400 mt-1">
                                📍 {team.location_name} • 👥 {team.members} Volunteers
                              </div>
                              <div className="text-[9px] text-sky-400 mt-0.5 truncate">
                                Lead: {team.leader_name} ({team.contact_phone})
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* 3. MATCHING HELP REQUESTS FEED (AI RISK PRIORITIZED) */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs px-1">
                        <span className="font-extrabold text-white flex items-center gap-1.5">
                          <span>📦</span> AI Risk-Prioritized Citizen Help Requests ({reliefRequests.length})
                        </span>
                        <span className="text-amber-400 text-[10px] font-mono">
                          Sorted by AI Risk & Urgency Score
                        </span>
                      </div>

                      {reliefRequests.length === 0 ? (
                        <div className="p-4 text-center text-xs text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800">
                          No pending help requests logged in the system.
                        </div>
                      ) : (
                        reliefRequests.slice().sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0)).map(req => {
                          const isPending = req.status === 'Pending' || req.status === 'SUBMITTED';
                          const isAssigned = req.status === 'Assigned' || req.status === 'In Progress';
                          const isCompleted = req.status === 'Completed' || req.status === 'Resolved';
                          const isEscalated = req.notes && req.notes.includes('ESCALATED');

                          const prioColor = (req.priority_score >= 85 || req.priority === 'Critical')
                            ? 'border-red-500/60 bg-red-950/20'
                            : (req.priority_score >= 70 || req.priority === 'High')
                            ? 'border-amber-500/60 bg-amber-950/20'
                            : 'border-slate-800 bg-slate-900/60';

                          const badgeStyle = (req.priority_score >= 85 || req.priority === 'Critical')
                            ? 'bg-red-600 text-white'
                            : (req.priority_score >= 70 || req.priority === 'High')
                            ? 'bg-amber-600 text-white'
                            : 'bg-slate-700 text-slate-200';

                          return (
                            <div key={req.id} className={`glass-card p-3 rounded-xl border space-y-2 text-xs transition-all ${prioColor}`}>
                              
                              {/* Request Header */}
                              <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-2">
                                <div>
                                  <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
                                    <span>📍</span> {req.location_name}
                                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-slate-800 text-slate-300">
                                      {req.request_code}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-slate-400 mt-0.5">
                                    Need Category: <strong className="text-amber-300 font-bold">{req.category}</strong> • People Count: <strong className="text-white font-bold">👥 {req.people_count || 1}</strong>
                                  </div>
                                </div>

                                <div className="flex flex-col items-end gap-1">
                                  <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${badgeStyle}`}>
                                    Score: {req.priority_score ? req.priority_score.toFixed(1) : '75.0'} ({req.priority || 'High'})
                                  </span>
                                  <span className={`px-1.5 py-0.2 rounded text-[8px] font-bold ${
                                    isCompleted ? 'bg-emerald-900 text-emerald-300' : isAssigned ? 'bg-purple-900 text-purple-300' : 'bg-amber-900 text-amber-300'
                                  }`}>
                                    {req.status} {req.assigned_team_name ? `(${req.assigned_team_name})` : ''}
                                  </span>
                                </div>
                              </div>

                              {/* Original SOS Message */}
                              <div className="p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-300">
                                <span className="text-[9px] uppercase font-extrabold text-slate-400 block mb-0.5">Original Citizen SOS Message / Need Detail:</span>
                                "{req.notes || req.description || 'Urgent community aid requested'}"
                              </div>

                              {/* Actions Bar */}
                              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-[10px]">
                                
                                {/* Communication Actions */}
                                <div className="flex items-center gap-1.5">
                                  <button
                                    onClick={() => setCommunityMessageModal({ open: true, request: req, text: '' })}
                                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1"
                                  >
                                    <span>💬</span> Message
                                  </button>
                                  <button
                                    onClick={() => {
                                      if (leafletMapRef.current && req.latitude && req.longitude) {
                                        leafletMapRef.current.flyTo([req.latitude, req.longitude], 16, { duration: 1.0 });
                                      }
                                      navigator.clipboard?.writeText?.(`GPS: ${req.latitude}, ${req.longitude} (${req.location_name})`);
                                      setLiveBanner({
                                        title: '📍 Location Shared',
                                        text: `GPS coordinates for ${req.location_name} copied & focused on map!`,
                                        type: 'info'
                                      });
                                    }}
                                    className="px-2 py-1 rounded bg-sky-950 hover:bg-sky-900 text-sky-200 border border-sky-800 flex items-center gap-1"
                                  >
                                    <span>📍</span> Share Location
                                  </button>
                                </div>

                                {/* Main Action Buttons */}
                                <div className="flex items-center gap-1.5">
                                  {isPending && (
                                    <button
                                      disabled={isUpdatingStatus}
                                      onClick={async () => {
                                        try {
                                          setIsUpdatingStatus(true);
                                          const team = currentTeam || communityTeams[0];
                                          const res = await fetch(`${API_BASE}/relief/requests/${req.id}/accept`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                              team_id: team ? team.id : null,
                                              team_name: team ? team.name : 'Community Volunteer Team'
                                            })
                                          });
                                          if (res.ok) {
                                            fetchAllData();
                                            if (leafletMapRef.current && req.latitude && req.longitude) {
                                              leafletMapRef.current.flyTo([req.latitude, req.longitude], 15, { duration: 1.0 });
                                            }
                                          }
                                        } finally {
                                          setIsUpdatingStatus(false);
                                        }
                                      }}
                                      className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold shadow-md shadow-emerald-600/30 flex items-center gap-1 disabled:opacity-50"
                                    >
                                      <span>🤝</span> Accept Request
                                    </button>
                                  )}

                                  {isAssigned && (
                                    <button
                                      disabled={isUpdatingStatus}
                                      onClick={async () => {
                                        try {
                                          setIsUpdatingStatus(true);
                                          const res = await fetch(`${API_BASE}/relief/requests/${req.id}/complete`, {
                                            method: 'POST'
                                          });
                                          if (res.ok) fetchAllData();
                                        } finally {
                                          setIsUpdatingStatus(false);
                                        }
                                      }}
                                      className="px-3 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-extrabold shadow-md flex items-center gap-1 disabled:opacity-50"
                                    >
                                      <span>✅</span> Mark Help Delivered
                                    </button>
                                  )}

                                  {!isCompleted && !isEscalated && (
                                    <button
                                      disabled={isUpdatingStatus}
                                      onClick={async () => {
                                        try {
                                          setIsUpdatingStatus(true);
                                          const res = await fetch(`${API_BASE}/relief/requests/${req.id}/escalate`, {
                                            method: 'POST'
                                          });
                                          if (res.ok) fetchAllData();
                                        } finally {
                                          setIsUpdatingStatus(false);
                                        }
                                      }}
                                      className="px-2 py-1 rounded bg-red-950 hover:bg-red-900 text-red-200 border border-red-800 font-bold flex items-center gap-1 disabled:opacity-50"
                                      title="Escalate to official NDRF / SDRF rescue taskforce"
                                    >
                                      <span>🚨</span> Escalate to NDRF
                                    </button>
                                  )}
                                </div>

                              </div>

                            </div>
                          );
                        })
                      )}

                    </div>

                  </div>
                );
              })()}
                </div>
              )}


        </div>
      </div>


      {/* 4. INTERACTIVE MULTILINGUAL SOS NLP TEST MODAL */}
      {showNLPModal && (
        <SOSAnalyzeModal
          onClose={() => setShowNLPModal(false)}
          onSOSSubmitted={() => {
            fetchAllData();
            setShowNLPModal(false);
          }}
        />
      )}

      {/* 5. NEW RELIEF REQUEST SUBMISSION MODAL */}
      {showNewRequestModal && (
        <NewReliefRequestModal
          onClose={() => setShowNewRequestModal(false)}
          onRequestSubmitted={() => {
            fetchAllData();
            setShowNewRequestModal(false);
          }}
        />
      )}

      {/* 6. MOCK DONATION & FUNDRAISING MODAL */}
      {showDonateModal && (
        <DonateModal
          onClose={() => setShowDonateModal(false)}
          onDonationComplete={() => {
            fetchAllData();
          }}
        />
      )}

      {/* 7. COMMUNITY MESSAGE / COMMUNICATION DISPATCH MODAL */}
      {communityMessageModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="glass-panel w-full max-w-sm rounded-2xl border border-sky-500/50 shadow-2xl p-4 space-y-3 bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-xs text-white flex items-center gap-1">
                <span>💬</span> Direct Communication Dispatch
              </span>
              <button onClick={() => setCommunityMessageModal({ open: false, request: null, text: '' })} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            <div className="text-[11px] text-slate-300">
              Sending direct dispatch message to field coordinator for <strong>{communityMessageModal.request?.location_name}</strong>:
            </div>
            <textarea
              rows={3}
              value={communityMessageModal.text}
              onChange={e => setCommunityMessageModal({ ...communityMessageModal, text: e.target.value })}
              placeholder="Type dispatch note or SMS instruction..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white text-xs"
            />
            <div className="flex justify-end gap-2 text-xs pt-1">
              <button
                onClick={() => setCommunityMessageModal({ open: false, request: null, text: '' })}
                className="px-3 py-1 rounded bg-slate-800 text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (communityMessageModal.request && communityMessageModal.text.trim()) {
                    await fetch(`${API_BASE}/relief/requests/${communityMessageModal.request.id}`, {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        notes: `${communityMessageModal.request.notes || ''} [DISPATCH NOTE: ${communityMessageModal.text}]`
                      })
                    });
                    fetchAllData();
                  }
                  setCommunityMessageModal({ open: false, request: null, text: '' });
                }}
                className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold"
              >
                Send Instruction
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// =====================================================================
// SOS ANALYZE / SUBMIT SANDBOX MODAL (SIH DEMO INTERFACE)
// =====================================================================
function SOSAnalyzeModal({ onClose, onSOSSubmitted }) {
  const [inputText, setInputText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  // Sample quick-fill buttons for SIH demo testing
  const sampleMessages = [
    { label: 'Telugu (Native)', text: 'మా ఇంట్లో నీళ్ళు వచ్చాయి, మా అమ్మకు ఇన్సులిన్ కావాలి' },
    { label: 'Telugu (Tenglish)', text: 'Meeru vacchi maaku help cheseyandi, amma ki insulin kavali' },
    { label: 'Hindi (Native)', text: 'हमारे घर में पानी आ गया है और मेरी माँ को दवाई चाहिए' },
    { label: 'Hindi (Hinglish)', text: 'Hamare ghar mein paani aa gaya hai, maa ko dawai chahiye urgently' },
    { label: 'Tamil', text: 'நாங்கள் வெள்ளத்தில் மாட்டிக்கொண்டோம், உடனடி உதவி தேவை' },
    { label: 'Kannada', text: 'ನಮ್ಮ ಮನೆಯಲ್ಲಿ ನೀರು ತುಂಬಿದೆ, ತಕ್ಷಣ ಸಹಾಯ ಮಾಡಿ' },
    { label: 'Malayalam', text: 'വെള്ളപ്പൊക്കം ഞങ്ങളെ കുടുക്കി, ഉടനടി ರਕ்ഷ വേണം' },
    { label: 'English', text: 'Water entered our house. My mother needs medicine urgently.' }
  ];

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;
    try {
      setIsAnalyzing(true);
      setStatusMsg('');
      const res = await fetch(`${API_BASE}/sos/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputText })
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
      } else {
        setStatusMsg('Error analyzing message');
      }
    } catch (err) {
      setStatusMsg('Network error during analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmitSOS = async () => {
    if (!inputText.trim()) return;
    try {
      setIsSubmitting(true);
      setStatusMsg('');
      // Use centroid coordinates of Vijayawada sector with slight random jitter
      const lat = 16.506 + (Math.random() - 0.5) * 0.02;
      const lon = 80.638 + (Math.random() - 0.5) * 0.02;

      const res = await fetch(`${API_BASE}/sos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputText,
          latitude: lat,
          longitude: lon
        })
      });

      if (res.ok) {
        setStatusMsg('SOS successfully submitted to RakshaNet Operations Grid!');
        setTimeout(() => {
          if (onSOSSubmitted) onSOSSubmitted();
        }, 1000);
      } else {
        setStatusMsg('Failed to submit SOS report');
      }
    } catch (err) {
      setStatusMsg('Network error submitting SOS');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌐</span>
            <div>
              <h2 className="font-bold text-white text-sm">Multilingual SOS NLP Sandbox</h2>
              <p className="text-[11px] text-slate-400">
                Test Indian language distress extraction without external API dependencies
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-lg px-2">
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 overflow-y-auto space-y-4 flex-1 text-xs">
          
          {/* Quick-fill buttons */}
          <div>
            <div className="text-[11px] font-bold text-slate-400 mb-1.5 uppercase">
              Quick Test Scenarios (All 6 Languages + Transliteration)
            </div>
            <div className="flex flex-wrap gap-1.5">
              {sampleMessages.map((s, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInputText(s.text);
                    setAnalysisResult(null);
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px]"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Distress Textarea */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Enter Citizen Distress Message (Native script or Roman letters):
            </label>
            <textarea
              rows={3}
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              placeholder="e.g., మా ఇంట్లో నీళ్ళు వచ్చాయి, మా అమ్మకు ఇన్సులిన్ కావాలి..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-xs"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !inputText.trim()}
              className="flex-1 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-md shadow-blue-600/30 disabled:opacity-50"
            >
              {isAnalyzing ? 'Analyzing...' : '🔍 Analyze with AI NLP'}
            </button>
            <button
              onClick={handleSubmitSOS}
              disabled={isSubmitting || !inputText.trim()}
              className="py-2 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold transition-all shadow-md shadow-red-600/30 disabled:opacity-50"
            >
              {isSubmitting ? 'Posting...' : '🚨 Submit to Grid'}
            </button>
          </div>

          {statusMsg && (
            <div className="p-2 rounded bg-blue-900/40 border border-blue-700 text-blue-300 text-center font-semibold">
              {statusMsg}
            </div>
          )}

          {/* Live NLP Results Display */}
          {analysisResult && (
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
              <div className="font-bold text-slate-200 text-xs flex items-center justify-between border-b border-slate-800 pb-1.5">
                <span>Structured Intelligence Extraction</span>
                <span className="text-emerald-400 font-mono">100% Local Pattern Engine</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded bg-slate-900">
                  <span className="text-slate-400">Detected Language:</span>
                  <div className="font-bold text-white text-xs mt-0.5">
                    {analysisResult.language_name} ({analysisResult.detected_language.toUpperCase()})
                    {analysisResult.is_transliterated && ' • Transliterated'}
                  </div>
                </div>

                <div className="p-2 rounded bg-slate-900">
                  <span className="text-slate-400">Emergency Urgency:</span>
                  <div className="font-bold text-red-400 text-xs mt-0.5 uppercase">
                    {analysisResult.urgency} ({analysisResult.priority_score}/100)
                  </div>
                </div>

                <div className="p-2 rounded bg-slate-900">
                  <span className="text-slate-400">Need Classification:</span>
                  <div className="font-bold text-amber-400 text-xs mt-0.5 capitalize">
                    {analysisResult.need_type}
                  </div>
                </div>

                <div className="p-2 rounded bg-slate-900">
                  <span className="text-slate-400">People Count:</span>
                  <div className="font-bold text-slate-200 text-xs mt-0.5">
                    {analysisResult.people_count || '1+ individuals'}
                  </div>
                </div>
              </div>

              {analysisResult.danger_factors && analysisResult.danger_factors.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase font-bold text-red-400 mb-1">
                    Life-Safety Danger Triggers:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {analysisResult.danger_factors.map((df, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-300 font-semibold text-[10px]">
                        ⚠️ {df.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-right">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}

// =====================================================================
// PHASE 8: NEW RELIEF REQUEST SUBMISSION MODAL
// =====================================================================
function NewReliefRequestModal({ onClose, onRequestSubmitted }) {
  const [category, setCategory] = useState('Drinking Water');
  const [priority, setPriority] = useState('High');
  const [peopleCount, setPeopleCount] = useState(25);
  const [locationName, setLocationName] = useState('Bhavanipuram Lowlands (Sector 2)');
  const [latitude, setLatitude] = useState(16.5230);
  const [longitude, setLongitude] = useState(80.5980);
  const [description, setDescription] = useState('Urgent drinking water supply and purification packets required for cut-off families.');
  const [requesterName, setRequesterName] = useState('Resident Coordinator');
  const [contactPhone, setContactPhone] = useState('+91 98480 22334');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!locationName.trim() || !description.trim()) {
      setErrorMsg('Please enter location and description');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg('');
      const res = await fetch(`${API_BASE}/relief/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          priority,
          people_count: Number(peopleCount) || 1,
          location_name: locationName,
          latitude: Number(latitude),
          longitude: Number(longitude),
          description,
          requester_name: requesterName,
          contact_phone: contactPhone,
        })
      });

      if (res.ok) {
        onRequestSubmitted();
      } else {
        const err = await res.json().catch(() => ({}));
        setErrorMsg(err.detail || 'Failed to submit relief request');
      }
    } catch (err) {
      console.error('Error submitting relief request:', err);
      setErrorMsg('Network error while submitting request');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-md rounded-2xl border border-emerald-500/50 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-3.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">📦</span>
            <div>
              <h2 className="font-bold text-sm text-white">Submit Emergency Relief Request</h2>
              <p className="text-[10px] text-slate-400">Pushes to field logistics depot and computes priority score</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xs px-2 py-1">✕</button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-4 overflow-y-auto space-y-3 text-xs flex-1">
          {errorMsg && (
            <div className="p-2 rounded bg-red-950/80 border border-red-800 text-red-300 text-center">
              {errorMsg}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Category</label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              >
                <option value="Food & Rations">Food & Rations</option>
                <option value="Drinking Water">Drinking Water</option>
                <option value="Medical & Insulin">Medical & Insulin</option>
                <option value="Shelter & Tarpaulins">Shelter & Tarpaulins</option>
                <option value="Search & Boat Rescue">Search & Boat Rescue</option>
                <option value="Sanitation & Hygiene">Sanitation & Hygiene</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Urgency Priority</label>
              <select
                value={priority}
                onChange={e => setPriority(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              >
                <option value="Critical">Critical (Immediate Life Threat)</option>
                <option value="High">High (Urgent Need)</option>
                <option value="Medium">Medium (Moderate Need)</option>
                <option value="Low">Low (General Supply)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Affected People</label>
              <input
                type="number"
                min="1"
                value={peopleCount}
                onChange={e => setPeopleCount(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Contact Phone</label>
              <input
                type="text"
                value={contactPhone}
                onChange={e => setContactPhone(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Location / Landmark</label>
            <input
              type="text"
              value={locationName}
              onChange={e => setLocationName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Description of Need</label>
            <textarea
              rows={2}
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={e => setLatitude(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={e => setLongitude(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Requester Name</label>
            <input
              type="text"
              value={requesterName}
              onChange={e => setRequesterName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/30 disabled:opacity-50"
            >
              {isSubmitting ? 'Dispatching...' : 'Submit Request'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}

// =====================================================================
// PHASE 8: MOCK FUNDRAISING & DONATION MODAL
// =====================================================================
function DonateModal({ onClose, onDonationComplete }) {
  const [donorName, setDonorName] = useState('Anonymized Citizen Supporter');
  const [amount, setAmount] = useState(5000);
  const [category, setCategory] = useState('Medical Supplies & Trauma Kits');
  const [message, setMessage] = useState('Supporting disaster relief efforts in affected zones.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successData, setSuccessData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!amount || amount <= 0) {
      setErrorMsg('Please enter a valid donation amount');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg('');
      const res = await fetch(`${API_BASE}/relief/donations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          donor_name: donorName,
          amount: Number(amount),
          category: category,
          message: message
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessData(data);
        if (onDonationComplete) onDonationComplete(data);
      } else {
        const err = await res.json().catch(() => ({}));
        setErrorMsg(err.detail || 'Failed to process mock donation');
      }
    } catch (err) {
      console.error('Error processing donation:', err);
      setErrorMsg('Network error while processing mock donation');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-md rounded-2xl border border-amber-500/50 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-3.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">💰</span>
            <div>
              <h2 className="font-bold text-sm text-white">Relief Contribution (Demo / Mock)</h2>
              <p className="text-[10px] text-slate-400">Simulated civic fundraising & emergency aid contribution</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xs px-2 py-1">✕</button>
        </div>

        {/* Modal Content */}
        {successData ? (
          <div className="p-6 text-center space-y-4 my-auto">
            <div className="text-4xl">🎉</div>
            <h3 className="font-bold text-emerald-400 text-base">Contribution Recorded Successfully!</h3>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-left space-y-1.5 font-mono">
              <div className="flex justify-between text-slate-400">
                <span>Reference ID:</span>
                <span className="text-amber-400 font-bold">{successData.reference_id}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Donor:</span>
                <span className="text-white">{successData.donor_name}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Amount:</span>
                <span className="text-emerald-400 font-bold">₹{successData.amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Target Bucket:</span>
                <span className="text-sky-300">{successData.category}</span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400">
              * Note: This is a prototype demonstration transaction. No actual funds were transferred.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 overflow-y-auto space-y-3 text-xs flex-1">
            {errorMsg && (
              <div className="p-2 rounded bg-red-950/80 border border-red-800 text-red-300 text-center">
                {errorMsg}
              </div>
            )}

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Donor Name / Organization</label>
              <input
                type="text"
                value={donorName}
                onChange={e => setDonorName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Select Contribution Amount (₹)</label>
              <div className="grid grid-cols-4 gap-1.5 mb-2">
                {[1000, 2500, 5000, 10000].map(amt => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setAmount(amt)}
                    className={`py-1.5 rounded-lg border text-xs font-bold transition-all ${
                      amount === amt
                        ? 'bg-amber-600 border-amber-400 text-white shadow'
                        : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    ₹{amt >= 10000 ? '10k' : amt.toLocaleString()}
                  </button>
                ))}
              </div>
              <input
                type="number"
                min="100"
                value={amount}
                onChange={e => setAmount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs font-mono font-bold"
                placeholder="Custom Amount"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Fund Allocation Focus</label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              >
                <option value="Food Rations & Water Rations">Food Rations & Water Rations</option>
                <option value="Medical Supplies & Trauma Kits">Medical Supplies & Trauma Kits</option>
                <option value="Emergency Temporary Shelters">Emergency Temporary Shelters</option>
                <option value="Critical Infrastructure Repair">Critical Infrastructure Repair</option>
                <option value="Direct Victim Emergency Cash">Direct Victim Emergency Cash</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Encouragement / Solidarity Note</label>
              <textarea
                rows={2}
                value={message}
                onChange={e => setMessage(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white text-xs"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-md shadow-amber-600/30 disabled:opacity-50 flex items-center gap-1"
              >
                <span>💰</span> {isSubmitting ? 'Processing...' : `Donate ₹${amount.toLocaleString()} (Demo)`}
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}

// Global Error Boundary to prevent React from ever rendering a blank page
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[RakshaNet Command Center Runtime Error]", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-950 text-slate-200 p-6">
          <div className="bg-slate-900 border border-red-500/50 p-6 rounded-2xl max-w-lg shadow-2xl text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-lg font-bold text-white">RakshaNet Command Center Notice</h2>
            <p className="text-xs text-slate-400">
              {this.state.error?.message || "A temporary rendering issue occurred. Data stream is still active."}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Render the application to DOM with Error Boundary protection
ReactDOM.createRoot(document.getElementById('root')).render(
  <ErrorBoundary>
    <RakshaNetApp />
  </ErrorBoundary>
);

