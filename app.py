# ============================================================
            # HEALTH REPORT - COMPONENT BREAKDOWN
            # ============================================================
            health_report = design_results.get("health_report", {})
            
            # Get beam data for CHS display - with debugging
            beam = design_results.get("beams", {}).get("main")
            selected_section = design_results.get("beams", {}).get("selected", "N/A")
            section_type = design_results.get("beams", {}).get("section_type", "N/A")
            is_adequate = design_results.get("beams", {}).get("is_adequate", False)
            
            # ALWAYS show member section status as a separate card
            if selected_section != "N/A":
                section_tag = get_section_tag(section_type)
                pass_status = "✅ PASS" if is_adequate else "⚠️ CHECK"
                st.markdown(f"""
                <div class="sds-card">
                    <div class="title">🔧 Member Section Status</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0;">
                        <div>
                            <span style="color: #ffffff; font-size: 1.1rem; font-weight: 600;">{selected_section}</span>
                            {section_tag}
                        </div>
                        <div>
                            <span style="color: {'#2ecc71' if is_adequate else '#f39c12'}; font-weight: 600;">
                                {pass_status}
                            </span>
                        </div>
                    </div>
                    <div style="color: #8a9aaa; font-size: 0.85rem;">
                        Section Type: {section_type} | {beam.get('note', '') if beam else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if health_report:
                st.markdown("## 🏥 Component Health Report")
                
                for component, data in health_report.get("components", {}).items():
                    score = data.get("score", 0)
                    status = data.get("status", "⚠️ CHECK")
                    
                    if score >= 90:
                        color = "#2ecc71"
                        emoji = "✅"
                    elif score >= 70:
                        color = "#f39c12"
                        emoji = "⚠️"
                    else:
                        color = "#e74c3c"
                        emoji = "❌"
                    
                    details = data.get("details", {})
                    detail_text = ""
                    if details:
                        detail_items = []
                        for k, v in details.items():
                            if isinstance(v, (int, float)):
                                if k.lower() in ['utilization', 'utilization_percent', 'reduction']:
                                    v = f"{v:.0f}%"
                                elif k.lower() in ['strength']:
                                    v = f"{v:.0f} kN/m"
                                else:
                                    v = f"{v:.0f}"
                            detail_items.append(f"{k}: {v}")
                        detail_text = " | ".join(detail_items)
                    
                    st.markdown(f"""
                    <div class="health-report-row">
                        <span class="component">{component}</span>
                        <span class="score" style="color: {color};">{emoji} {score:.0f}%</span>
                        <span class="status">{status}</span>
                        <span class="details">{detail_text}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
