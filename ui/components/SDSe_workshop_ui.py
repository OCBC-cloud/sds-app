import streamlit as st
import streamlit.components.v1 as components

def render_floating_toolbar():
    """
    Renders the One Page Workshop 3D viewer with the floating toolbar.
    """
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            body { margin: 0; overflow: hidden; background-color: #0d1117; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            canvas { display: block; width: 100vw; height: 100vh; }
            .floating-toolbar {
                position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
                background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px;
                display: flex; gap: 16px; padding: 12px 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); z-index: 100; transition: opacity 0.3s ease;
            }
            .floating-toolbar.interacting { opacity: 0.2; }
            .tool-icon { width: 24px; height: 24px; fill: #8b949e; cursor: pointer; transition: fill 0.2s ease, transform 0.1s ease; }
            .tool-icon:hover, .tool-icon:active { fill: #ffffff; transform: scale(1.1); }
            .axis-labels {
                position: absolute; bottom: 90px; width: 100%; display: flex; justify-content: space-between;
                padding: 0 40px; box-sizing: border-box; color: #8b949e; font-size: 12px; font-weight: 500; pointer-events: none;
            }
        </style>
    </head>
    <body>
        <div class="axis-labels"><span>X (m)</span><span>Y (m)</span></div>
        <div class="floating-toolbar" id="toolbar">
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10z"/></svg>
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M12 2l2.4 7.2h7.6l-6.2 4.4 2.4 7.2-6.2-4.4-6.2 4.4 2.4-7.2-6.2-4.4h7.6z"/></svg>
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
            <svg class="tool-icon" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
        </div>
        <script type="importmap">
          { "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/" } }
        </script>
        <script type="module">
            import * as THREE from 'three';
            import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
            const scene = new THREE.Scene(); scene.background = new THREE.Color('#0d1117'); 
            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000); camera.position.set(10, 8, 15);
            const renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setSize(window.innerWidth, window.innerHeight); renderer.setPixelRatio(window.devicePixelRatio); document.body.appendChild(renderer.domElement);
            const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.dampingFactor = 0.05; controls.maxPolarAngle = Math.PI / 2 - 0.05; controls.minDistance = 5; controls.maxDistance = 40;
            const toolbar = document.getElementById('toolbar');
            controls.addEventListener('start', () => { toolbar.classList.add('interacting'); });
            controls.addEventListener('end', () => { toolbar.classList.remove('interacting'); });
            const gridHelper = new THREE.GridHelper(20, 20, 0x30363d, 0x21262d); gridHelper.position.y = -0.01; scene.add(gridHelper);
            scene.add(new THREE.AmbientLight(0xffffff, 0.6));
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8); directionalLight.position.set(10, 20, 10); scene.add(directionalLight);
            const surfaceGeometry = new THREE.CylinderGeometry(5.1, 5.1, 6, 32, 1, true, Math.PI/4, Math.PI/2);
            const surfaceMaterial = new THREE.MeshPhongMaterial({ color: 0x2ea043, transparent: true, opacity: 0.4, side: THREE.DoubleSide });
            const greenSurface = new THREE.Mesh(surfaceGeometry, surfaceMaterial); greenSurface.rotation.z = Math.PI / 2; greenSurface.position.y = 2.5; scene.add(greenSurface);
            const domeGeometry = new THREE.SphereGeometry(5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
            const domeMaterial = new THREE.MeshPhongMaterial({ color: 0x1f6feb, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
            const dome = new THREE.Mesh(domeGeometry, domeMaterial); scene.add(dome);
            const arcMaterial = new THREE.LineBasicMaterial({ color: 0xff7b72, linewidth: 2 });
            for (let i = 0; i < 6; i++) {
                const angle = (i / 6) * Math.PI; const points = [];
                for (let j = 0; j <= 32; j++) {
                    const t = j / 32; const phi = t * Math.PI;
                    points.push(new THREE.Vector3(Math.cos(angle) * Math.sin(phi) * 5.2, Math.cos(phi) * 5.2, Math.sin(angle) * Math.sin(phi) * 5.2));
                }
                scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), arcMaterial));
            }
            function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }
            window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
            animate();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=800, scrolling=False)
