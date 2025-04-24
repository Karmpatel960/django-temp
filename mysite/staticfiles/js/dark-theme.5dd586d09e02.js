// Check for saved theme preference or default to 'light'
const currentTheme = localStorage.getItem('theme') || 'light';

// Set the theme on initial load
document.documentElement.setAttribute('data-theme', currentTheme);

// Function to handle theme changes
function handleThemeChange(isDark) {
    if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        // Force text color updates for headings
        setTimeout(() => {
            const headings = document.querySelectorAll('.h1-large, .p-large');
            headings.forEach(heading => {
                if (heading.classList.contains('h1-large')) {
                    heading.style.color = '#ffffff';
                } else if (heading.classList.contains('p-large')) {
                    heading.style.color = '#e0e0e0';
                }
            });
        }, 50);
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        // Reset text color for headings
        setTimeout(() => {
            const headings = document.querySelectorAll('.h1-large, .p-large');
            headings.forEach(heading => {
                if (heading.classList.contains('h1-large')) {
                    heading.style.color = '#012970';
                } else if (heading.classList.contains('p-large')) {
                    heading.style.color = '#444444';
                }
            });
        }, 50);
    }
}

// Initialize theme toggle when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (!themeToggle) {
        console.error('Theme toggle element not found');
        return;
    }
    
    // Set initial toggle state
    themeToggle.checked = currentTheme === 'dark';
    
    // Apply initial text colors if dark mode
    if (currentTheme === 'dark') {
        const headings = document.querySelectorAll('.h1-large, .p-large');
        headings.forEach(heading => {
            if (heading.classList.contains('h1-large')) {
                heading.style.color = '#ffffff';
            } else if (heading.classList.contains('p-large')) {
                heading.style.color = '#e0e0e0';
            }
        });
    }
    
    // Event listener for theme switch
    themeToggle.addEventListener('change', (e) => {
        handleThemeChange(e.target.checked);
    });
    
    // Log successful initialization
    console.log('Theme system initialized with theme:', currentTheme);
}); 