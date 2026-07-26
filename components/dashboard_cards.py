import streamlit as st


def kpi_card(title, value, change, icon):

    st.metric(
        label=f"{icon} {title}",
        value=value,
        delta=change
    )



def factory_status(name, status):

    if status == "Running":

        st.success(
            f"🟢 {name}: Running"
        )


    elif status == "Warning":

        st.warning(
            f"🟡 {name}: Warning"
        )


    else:

        st.error(
            f"🔴 {name}: Offline"
        )



def notification(message):

    st.info(
        f"🔔 {message}"
    )
