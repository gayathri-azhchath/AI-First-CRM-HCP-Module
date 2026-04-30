import { configureStore, createSlice } from '@reduxjs/toolkit';

const interactionSlice = createSlice({
  name: 'interaction',
  initialState: {
    hcp_name: '',
    interaction_type: 'Meeting',
    date: new Date().toISOString().split('T')[0],
    time: '19:36', // Default from video
    attendees: '',
    topics: '',
    materials: [],
    samples: [],
    sentiment: 'Neutral',
    outcomes: '',
    follow_ups: '',
    messages: []
  },
  reducers: {
    setFormField: (state, action) => {
      state[action.payload.field] = action.payload.value;
    },
    syncState: (state, action) => {
      return { ...state, ...action.payload };
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    }
  }
});

export const { setFormField, syncState, addMessage } = interactionSlice.actions;
export const store = configureStore({ reducer: { interaction: interactionSlice.reducer } });