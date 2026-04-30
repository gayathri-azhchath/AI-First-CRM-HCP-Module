import { configureStore, createSlice } from '@reduxjs/toolkit';

// 1. Define the default empty state
const initialState = {
  hcp_name: '',
  interaction_type: 'Meeting',
  date: new Date().toISOString().split('T')[0],
  time: '19:36',
  attendees: '',
  topics: '',
  materials: [],
  samples: [],
  sentiment: 'Neutral',
  outcomes: '',
  follow_ups: '',
  messages: []
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setFormField: (state, action) => {
      state[action.payload.field] = action.payload.value;
    },
    syncState: (state, action) => {
      return { ...state, ...action.payload };
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    // 2. NEW: Add a reset action
    resetForm: () => {
      return initialState; 
    }
  }
});

// 3. Export the new resetForm action
export const { setFormField, syncState, addMessage, resetForm } = interactionSlice.actions;
export const store = configureStore({ reducer: { interaction: interactionSlice.reducer } });