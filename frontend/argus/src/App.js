import React, {Component, ScrollAnimation, useRef} from 'react';


import './App.css';

import { BrowserRouter as Router, Route, Routes} from 'react-router-dom'

import Home from './components/Home'
// import header from './components/header'
import About from './components/About'
import Application from './components/application'
import Modal from './components/application/Modal/'



function App() { 
    return (
      <div className='App'>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="application" element={<Application />} />
          <Route path="modal" element={<Modal />} />
        </Routes>
      </div>
    )
  
}
 
export default App;
