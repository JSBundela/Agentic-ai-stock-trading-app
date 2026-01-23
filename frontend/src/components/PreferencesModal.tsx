import React, { useState } from 'react';
import { getPreferences, savePreferences, resetPreferences, type UserPreferences } from '../utils/preferences';

interface Props {
    isOpen: boolean;
    onClose: () => void;
}

const PreferencesModal: React.FC<Props> = ({ isOpen, onClose }) => {
    const [prefs, setPrefs] = useState<UserPreferences>(getPreferences());
    const [saved, setSaved] = useState(false);

    if (!isOpen) return null;

    const handleSave = () => {
        savePreferences(prefs);
        setSaved(true);
        setTimeout(() => {
            setSaved(false);
            onClose();
        }, 1500);
    };

    const handleReset = () => {
        if (confirm('Reset all preferences to defaults?')) {
            resetPreferences();
            setPrefs(getPreferences());
        }
    };

    const styles = {
        overlay: {
            position: 'fixed' as const,
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
        },
        modal: {
            backgroundColor: '#2d2d2d',
            borderRadius: '8px',
            padding: '32px',
            maxWidth: '500px',
            width: '90%',
            border: '1px solid #3d3d3d'
        },
        header: {
            fontSize: '24px',
            fontWeight: 'bold',
            marginBottom: '24px',
            color: 'white'
        },
        section: {
            marginBottom: '20px'
        },
        label: {
            display: 'block',
            fontSize: '14px',
            fontWeight: '500',
            color: '#d1d5db',
            marginBottom: '8px'
        },
        select: {
            width: '100%',
            padding: '12px',
            backgroundColor: '#1a1a1a',
            border: '1px solid #3d3d3d',
            borderRadius: '6px',
            color: 'white',
            fontSize: '16px'
        },
        input: {
            width: '100%',
            padding: '12px',
            backgroundColor: '#1a1a1a',
            border: '1px solid #3d3d3d',
            borderRadius: '6px',
            color: 'white',
            fontSize: '16px'
        },
        toggle: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px',
            backgroundColor: '#1a1a1a',
            borderRadius: '6px'
        },
        buttons: {
            display: 'flex',
            gap: '12px',
            marginTop: '32px'
        },
        button: {
            flex: 1,
            padding: '12px',
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '500'
        },
        successBanner: {
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            border: '1px solid #10b981',
            color: '#6ee7b7',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
            textAlign: 'center' as const
        }
    };

    return (
        <div style={styles.overlay} onClick={onClose}>
            <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
                <h2 style={styles.header}>Trading Preferences</h2>

                {saved && (
                    <div style={styles.successBanner}>
                        ✓ Preferences saved successfully!
                    </div>
                )}

                <div style={styles.section}>
                    <label style={styles.label}>Default Order Type</label>
                    <select
                        value={prefs.defaultOrderType}
                        onChange={(e) => setPrefs({ ...prefs, defaultOrderType: e.target.value as 'LIMIT' | 'MARKET' })}
                        style={styles.select}
                    >
                        <option value="LIMIT">LIMIT</option>
                        <option value="MARKET">MARKET</option>
                    </select>
                </div>

                <div style={styles.section}>
                    <label style={styles.label}>Default Product</label>
                    <select
                        value={prefs.defaultProduct}
                        onChange={(e) => setPrefs({ ...prefs, defaultProduct: e.target.value })}
                        style={styles.select}
                    >
                        <option value="CNC">CNC (Delivery)</option>
                        <option value="MIS">MIS (Intraday)</option>
                        <option value="NRML">NRML (Normal)</option>
                    </select>
                </div>

                <div style={styles.section}>
                    <label style={styles.label}>Default Quantity</label>
                    <input
                        type="number"
                        value={prefs.defaultQuantity}
                        onChange={(e) => setPrefs({ ...prefs, defaultQuantity: parseInt(e.target.value) || 1 })}
                        min="1"
                        style={styles.input}
                    />
                </div>

                <div style={styles.section}>
                    <label style={styles.label}>Auto-Refresh Interval (seconds)</label>
                    <input
                        type="number"
                        value={prefs.refreshInterval}
                        onChange={(e) => setPrefs({ ...prefs, refreshInterval: parseInt(e.target.value) || 10 })}
                        min="5"
                        max="60"
                        style={styles.input}
                    />
                </div>

                <div style={styles.section}>
                    <div style={styles.toggle}>
                        <div>
                            <p style={{ fontWeight: '500', marginBottom: '4px', color: 'white' }}>Auto-Refresh Orders</p>
                            <p style={{ fontSize: '12px', color: '#9ca3af' }}>Automatically refresh order book</p>
                        </div>
                        <button
                            onClick={() => setPrefs({ ...prefs, autoRefreshOrders: !prefs.autoRefreshOrders })}
                            style={{
                                padding: '4px 8px',
                                backgroundColor: prefs.autoRefreshOrders ? '#10b981' : '#6b7280',
                                color: 'white',
                                borderRadius: '12px',
                                border: 'none',
                                cursor: 'pointer'
                            }}
                        >
                            {prefs.autoRefreshOrders ? 'ON' : 'OFF'}
                        </button>
                    </div>
                </div>

                <div style={styles.buttons}>
                    <button
                        onClick={handleReset}
                        style={{ ...styles.button, backgroundColor: '#6b7280', color: 'white' }}
                    >
                        Reset to Defaults
                    </button>
                    <button
                        onClick={handleSave}
                        style={{ ...styles.button, backgroundColor: '#2563eb', color: 'white' }}
                    >
                        Save Preferences
                    </button>
                </div>

                <button
                    onClick={onClose}
                    style={{
                        width: '100%',
                        marginTop: '12px',
                        padding: '12px',
                        backgroundColor: '#3d3d3d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '16px'
                    }}
                >
                    Close
                </button>
            </div>
        </div>
    );
};

export default PreferencesModal;
