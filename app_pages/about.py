import streamlit as st

from ui import show_page_title, show_section_title


def show_about():
    show_page_title(
        "About / System Information",
        "Overview of E-WARPS purpose, modules, users, and limitations."
    )

    show_section_title("System Name")

    st.markdown(
        """
        **E-WARPS** stands for **Earthquake Warning Alert and Response Prioritization System**.

        It is an **AI-assisted command decision support prototype** designed to help organize earthquake-related alerts,
        field incident reports, rescue prioritization, situation reporting, GIS visualization, and resource allocation.
        """
    )

    st.divider()

    show_section_title("System Purpose")

    st.markdown(
        """
        The purpose of E-WARPS is to support faster and more organized decision-making during earthquake response operations.

        The system helps users:

        - Record earthquake alert information
        - Submit field incident reports
        - Classify affected areas based on urgency
        - Visualize reports on a GIS-based map
        - Generate AI-assisted command recommendations
        - Produce situation reports
        - Track available response resources
        - Maintain an activity log or audit trail
        """
    )

    st.divider()

    show_section_title("Intended Users")

    st.markdown(
        """
        **Commander**
        - Reviews operational overview, prioritization, command recommendations, SITREP, and resources.

        **Operations Officer**
        - Records alerts, manages reports, reviews maps, prioritization, SITREP, and resources.

        **Responder**
        - Submits field incident reports with location, impact details, remarks, and photos.

        **Admin**
        - Has access to all modules, records, settings, and testing controls.
        """
    )

    st.divider()

    show_section_title("Main Modules")

    st.markdown(
        """
        **Dashboard**  
        Shows alerts, reports, affected areas, critical areas, and charts.

        **Earthquake Alerts**  
        Records earthquake alert data from official or authorized monitoring sources.

        **Incident Reports**  
        Records field reports, casualties, injured persons, trapped persons, damaged buildings, road status, remarks, photos, and coordinates.

        **Rescue Prioritization**  
        Ranks affected areas using a weighted urgency score.

        **GIS Map**  
        Displays incident reports on a map using submitted coordinates.

        **Command Recommendations**  
        Provides AI-assisted suggested actions based on priority level.

        **Situation Report**  
        Generates a command-style SITREP and PDF export.

        **Resource Allocation**  
        Records available response resources and suggests allocation priorities.

        **Activity Log / Audit Trail**  
        Records system activity for monitoring and accountability.
        """
    )

    st.divider()

    show_section_title("Priority Scoring Logic")

    st.markdown(
        """
        E-WARPS currently uses a rule-based scoring model.

        The system considers:

        - Number of casualties
        - Number of injured persons
        - Number of trapped persons
        - Number of damaged buildings
        - Road status

        Reports are classified into:

        **🔴 Critical** — immediate command attention required.  
        **🟠 Severe** — urgent assessment and response preparation required.  
        **🟡 Moderate** — monitoring and validation required.  
        **🟢 Low** — continued observation required.
        """
    )

    st.divider()

    show_section_title("AI-Assisted Function")

    st.markdown(
        """
        In this prototype, the AI-assisted component is represented through automated decision-support logic,
        generated command recommendations, rescue prioritization, situation report generation, and resource allocation suggestions.

        The system does **not** replace human command judgment. It only assists by organizing data and suggesting possible
        courses of action based on encoded information.
        """
    )

    st.warning(
        "Final decisions, deployment orders, and operational approval must always remain under authorized human command."
    )

    st.divider()

    show_section_title("Current Limitations")

    st.markdown(
        """
        This version is a capstone prototype and has the following limitations:

        - It does not generate actual earthquake predictions.
        - It does not replace official PHIVOLCS earthquake alerts.
        - It depends on manually encoded or user-submitted information.
        - Location accuracy depends on device GPS, geocoding, or manual coordinate input.
        - The current login system is for prototype demonstration only.
        - The priority score is rule-based and should be validated by responders or subject matter experts.
        - Internet connection may be required for geocoding and map-related functions.
        """
    )

    st.divider()

    show_section_title("Recommended Future Enhancements")

    st.markdown(
        """
        Possible future improvements include:

        - Integration with official earthquake alert feeds
        - Secure database-based user authentication
        - Hashed passwords and user account management
        - Offline-first field reporting
        - Mobile-friendly responder interface
        - ICS-style form generation
        - More advanced machine learning model trained using historical disaster response data
        - Additional GIS layers for hospitals, evacuation centers, roads, utilities, and hazard areas
        """
    )

    st.divider()

    show_section_title("System Disclaimer")

    st.info(
        """
        E-WARPS is designed as an AI-assisted decision support prototype for academic and demonstration purposes.
        It should support, not replace, official disaster response protocols, command judgment,
        engineering assessment, and coordination with authorized government agencies.
        """
    )