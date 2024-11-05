import datetime

import streamlit as st
import pandas as pd

CHANNELS = ['HBO',
            'HBO 2',
            'HBO 3',
            'Cinestar TV action thriller',
            'Cinestar TV fantasy',
            'Cinestar TV comedy',
            'Cinestar TV premiere 1',
            'Cinestar TV premiere 2']
START_DATE = datetime.date.today() - datetime.timedelta(days=7)
END_DATE = datetime.date.today()


st.set_page_config(page_title="TV raspored za prethodnu nedelju",
                   page_icon=":tv:",
                   layout="wide")


def load_df(channel: str) -> pd.DataFrame:
    """Loads data from the database for the selected tv channel."""
    table_name = channel.replace(' ', '_').capitalize()

    conn = st.connection("postgresql", type="sql")
    return conn.query('SELECT * FROM {}'.format(table_name), ttl="10m")


def prepare_for_display(df: pd.DataFrame,
                        start: datetime.date,
                        end: datetime.date) -> pd.DataFrame:
    """Transforms data for displaying in the app
    and creates a new dataframe."""
    df.sort_values('datetime', inplace=True)
    mask = [(d1 - d2).seconds < 301 for d1, d2 in
            zip(df.datetime[1:], df.datetime[:-1])] + [False]
    df.drop(df[mask].index, inplace=True)

    df['days'] = df.datetime.dt.date
    df['time'] = df.datetime.dt.strftime('%H:%M')
    df['display'] = df.time + ' ' + df.genre.str.rjust(7, ' ') + '   ' + df.title  # noqa

    date_range = pd.date_range(start, end)
    dfs = []
    for ts in date_range:
        d = df[df.days == ts.date()][['display']]
        d.reset_index(inplace=True, drop=True)
        dfs.append(d)

    date_display = [ts.strftime('%d. %h %w') for ts in date_range]
    translate = 'Nedelja Ponedeljak Utorak Sreda Četvrtak Petak Subota'.split()
    date_display_with_day_names = [
        date[:-1] + ' - ' + translate[int(date.split()[2])]
        for date in date_display]

    nd = pd.DataFrame({dt: d['display']
                       for dt, d in zip(date_display_with_day_names, dfs)})
    nd.fillna('', inplace=True)

    return nd


def main():
    st.title('Raspored tv programa do 7 dana unazad')

    channel = st.selectbox('Izaberi kanal', CHANNELS)

    dates = st.date_input(
        label='Izaberi datume',
        value=(START_DATE, END_DATE),
        min_value=START_DATE,
        max_value=END_DATE + datetime.timedelta(days=3),
        args=(START_DATE, END_DATE)
    )
    if len(dates) != 2:
        st.stop()

    start_date, end_date = dates
    raw_df = load_df(channel)
    display_df = prepare_for_display(raw_df, start_date, end_date)

    st.dataframe(display_df, width=3000, height=740, hide_index=True)


if __name__ == '__main__':
    main()
