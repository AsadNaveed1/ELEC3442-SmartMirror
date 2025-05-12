let calendarData = {
    events: [],
    eventsByDate: {}
};

async function fetchCalendarEvents() {
    try {
        const response = await fetch('http://localhost:5001/calendar');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        calendarData.events = data.events || [];
        calendarData.eventsByDate = data.events_by_date || {};
        
        updateCalendarWidget();
        updateCalendarModal();
        return data;
    } catch (error) {
        console.error('Error fetching calendar events:', error);
        return { events: [], events_by_date: {} };
    }
}

function updateCalendarWidget() {
    const widgetContent = document.getElementById('calendar-events');
    if (!widgetContent) return;
    
    const today = new Date();
    // Format the date to match exactly how it comes from the backend
    const todayStr = today.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
    
    console.log("Looking for events with date:", todayStr);
    console.log("Available dates in data:", Object.keys(calendarData.eventsByDate));
    
    const todayEvents = calendarData.eventsByDate[todayStr] || [];
    
    todayEvents.sort((a, b) => {
        if (a.all_day && !b.all_day) return -1;
        if (!a.all_day && b.all_day) return 1;
        return new Date(a.start) - new Date(b.start);
    });
    
    const eventsToShow = todayEvents.slice(0, 3);
    
    if (eventsToShow.length === 0) {
        widgetContent.innerHTML = '<div class="no-events">No events today</div>';
        return;
    }
    
    let html = '';
    eventsToShow.forEach(event => {
        html += `
            <div class="event">
                <div class="event-time">${event.time_str}</div>
                <div class="event-title">${event.summary}</div>
            </div>
        `;
    });
    
    if (todayEvents.length > 3) {
        html += `<div class="more-events">+${todayEvents.length - 3} more</div>`;
    }
    
    widgetContent.innerHTML = html;
}

function updateCalendarModal() {
    const container = document.getElementById('calendar-detailed');
    if (!container) return;
    
    const eventsByDate = {};
    
    calendarData.events.forEach(event => {
        const dateObj = new Date(event.start);
        const dateKey = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        
        if (!eventsByDate[dateKey]) {
            eventsByDate[dateKey] = [];
        }
        
        eventsByDate[dateKey].push(event);
    });
    
    const dates = Object.keys(eventsByDate).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    let html = '';
    
    if (dates.length === 0) {
        html = '<div class="no-events">No upcoming events found</div>';
    } else {
        dates.forEach(date => {
            const events = eventsByDate[date];
            
            const today = new Date();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            const dateObj = new Date(events[0].start);
            let dateLabel = date;
            
            if (dateObj.toDateString() === today.toDateString()) {
                dateLabel = 'Today - ' + date;
            } else if (dateObj.toDateString() === tomorrow.toDateString()) {
                dateLabel = 'Tomorrow - ' + date;
            }
            
            html += `<h3>${dateLabel}</h3><div style="margin-top: 15px;">`;
            
            events.sort((a, b) => {
                if (a.all_day && !b.all_day) return -1;
                if (!a.all_day && b.all_day) return 1;
                return new Date(a.start) - new Date(b.start);
            });
            
            events.forEach(event => {
                const colors = {
                    '1': '#7986cb',
                    '2': '#33b679',
                    '3': '#8e24aa',
                    '4': '#e67c73',
                    '5': '#f6bf26',
                    '6': '#f4511e',
                    '7': '#039be5',
                    '8': '#616161',
                    '9': '#3f51b5',
                    '10': '#0b8043',
                    '11': '#d50000',
                    'default': '#4285F4'
                };
                
                const color = colors[event.colorId] || colors.default;
                
                html += `
                    <div style="border-left: 4px solid ${color}; padding-left: 10px; margin-bottom: 15px;">
                        <div style="font-weight: bold;">${event.time_str}</div>
                        <div>${event.summary}</div>
                        ${event.location ? `<div style="opacity: 0.7;">${event.location}</div>` : ''}
                    </div>
                `;
            });
            
            html += '</div>';
        });
    }
    
    container.innerHTML = html;
}

function initCalendar() {
    fetchCalendarEvents();
    
    setInterval(fetchCalendarEvents, 30 * 60 * 1000);
    
    const calendarWidget = document.getElementById('schedule-widget');
    const calendarModal = document.getElementById('calendarModal');
    const closeBtn = calendarModal.querySelector('.close');
    
    if (calendarWidget && calendarModal) {
        calendarWidget.addEventListener('click', function() {
            updateCalendarModal();
            calendarModal.style.display = 'block';
        });
        
        closeBtn.addEventListener('click', function() {
            calendarModal.style.display = 'none';
        });
        
        window.addEventListener('click', function(event) {
            if (event.target === calendarModal) {
                calendarModal.style.display = 'none';
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', initCalendar);