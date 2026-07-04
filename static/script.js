document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const movieSearchInput = document.getElementById('movie-search-input');
    const autocompleteResults = document.getElementById('autocomplete-results');
    const clearSearchBtn = document.getElementById('clear-search-btn');
    const userIdInput = document.getElementById('user-id-input');
    const getUserRecBtn = document.getElementById('get-user-rec-btn');
    const loader = document.getElementById('loader');
    const resultsGrid = document.getElementById('results-grid');
    const contextPanel = document.getElementById('context-panel');
    const contextTitle = document.getElementById('context-title');
    const contextHistory = document.getElementById('context-history');
    const suggestBtns = document.querySelectorAll('.suggest-btn');

    let debounceTimeout = null;

    // --- Tab Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Toggle active buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle active contents
            tabContents.forEach(content => {
                if (content.id === targetTab) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
            
            // Clear current inputs and results when switching views
            clearSearchState();
        });
    });

    // --- Movie Search Autocomplete ---
    movieSearchInput.addEventListener('input', () => {
        const query = movieSearchInput.value.trim();
        
        if (query.length > 0) {
            clearSearchBtn.style.display = 'block';
        } else {
            clearSearchBtn.style.display = 'none';
        }

        clearTimeout(debounceTimeout);
        if (query.length < 2) {
            autocompleteResults.innerHTML = '';
            return;
        }

        debounceTimeout = setTimeout(() => {
            fetch(`/api/movies?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    renderAutocomplete(data);
                })
                .catch(err => console.error('Error fetching autocomplete:', err));
        }, 200);
    });

    // Clear search
    clearSearchBtn.addEventListener('click', () => {
        movieSearchInput.value = '';
        clearSearchBtn.style.display = 'none';
        autocompleteResults.innerHTML = '';
        clearSearchState();
    });

    // Close autocomplete on clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            autocompleteResults.innerHTML = '';
        }
    });

    function renderAutocomplete(movies) {
        autocompleteResults.innerHTML = '';
        if (movies.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'autocomplete-item';
            emptyItem.style.cursor = 'default';
            emptyItem.innerHTML = `<div class="item-title" style="color: var(--text-muted);">No matches found</div>`;
            autocompleteResults.appendChild(emptyItem);
            return;
        }

        movies.forEach(movie => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            
            const releaseYear = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
            const genresList = movie.parsed_genres ? movie.parsed_genres.slice(0, 2).join(', ') : '';
            const typeLabel = movie.type === 'movie' ? 'Movie' : 'TV Show';
            const typeClass = movie.type === 'movie' ? 'badge-movie' : 'badge-tv';

            item.innerHTML = `
                <div class="item-title" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <span>${escapeHtml(movie.title)}</span>
                    <span class="type-badge ${typeClass}">${typeLabel}</span>
                </div>
                <div class="item-meta">${releaseYear} • ${escapeHtml(genresList)}</div>
            `;

            item.addEventListener('click', () => {
                movieSearchInput.value = movie.title;
                autocompleteResults.innerHTML = '';
                if (movie.type === 'movie') {
                    fetchRecommendationsByMovie(movie.id, movie.title);
                } else {
                    fetchRecommendationsByTV(movie.id, movie.title);
                }
            });

            autocompleteResults.appendChild(item);
        });
    }

    // --- Fetch Movie-to-Movie Recommendations ---
    function fetchRecommendationsByMovie(movieId, title) {
        showLoader();
        resultsGrid.innerHTML = '';
        contextPanel.style.display = 'none';

        fetch(`/api/recommend/movie/${movieId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch recommendations');
                return res.json();
            })
            .then(data => {
                hideLoader();
                renderContextPanel('similar', { title: title });
                renderRecommendations(data.recommendations);
            })
            .catch(err => {
                hideLoader();
                renderError('Could not retrieve recommendations. Please try again.');
                console.error(err);
            });
    }

    // --- Fetch TV-to-TV Recommendations ---
    function fetchRecommendationsByTV(tvId, title) {
        showLoader();
        resultsGrid.innerHTML = '';
        contextPanel.style.display = 'none';

        fetch(`/api/recommend/tv/${tvId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch recommendations');
                return res.json();
            })
            .then(data => {
                hideLoader();
                renderContextPanel('similar_tv', { title: title });
                renderRecommendations(data.recommendations);
            })
            .catch(err => {
                hideLoader();
                renderError('Could not retrieve recommendations. Please try again.');
                console.error(err);
            });
    }

    // --- User-Personalized Recommendations ---
    getUserRecBtn.addEventListener('click', () => {
        const userId = parseInt(userIdInput.value);
        if (isNaN(userId) || userId < 1 || userId > 610) {
            alert('Please enter a valid Client ID between 1 and 610.');
            return;
        }
        fetchRecommendationsByUser(userId);
    });

    // Handle pressing Enter inside Client ID input
    userIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            getUserRecBtn.click();
        }
    });

    // Quick suggest buttons
    suggestBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const uid = btn.getAttribute('data-uid');
            userIdInput.value = uid;
            fetchRecommendationsByUser(parseInt(uid));
        });
    });

    function fetchRecommendationsByUser(userId) {
        showLoader();
        resultsGrid.innerHTML = '';
        contextPanel.style.display = 'none';

        fetch(`/api/recommend/user/${userId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch recommendations');
                return res.json();
            })
            .then(data => {
                hideLoader();
                renderContextPanel('user', { userId: userId, liked: data.user_liked_movies });
                renderRecommendations(data.recommendations);
            })
            .catch(err => {
                hideLoader();
                renderError('Could not retrieve personalized recommendations. Check backend logs.');
                console.error(err);
            });
    }

    // --- UI Helpers ---
    function showLoader() {
        loader.style.display = 'block';
    }

    function hideLoader() {
        loader.style.display = 'none';
    }

    function clearSearchState() {
        resultsGrid.innerHTML = `
            <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="sparkles-icon"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                <h3>Ready to Recommend</h3>
                <p>Search for a title you love or select a Client ID to see AI-driven recommendations instantly.</p>
            </div>
        `;
        contextPanel.style.display = 'none';
    }

    function renderContextPanel(type, info) {
        contextPanel.style.display = 'block';
        contextHistory.innerHTML = '';

        if (type === 'similar') {
            contextTitle.textContent = 'Recommendations based on your choice:';
            contextHistory.innerHTML = `
                <div class="context-chip">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M17 3v18"/></svg>
                    ${escapeHtml(info.title)} (Movie)
                </div>
            `;
        } else if (type === 'similar_tv') {
            contextTitle.textContent = 'Recommendations based on your choice:';
            contextHistory.innerHTML = `
                <div class="context-chip">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="15" x="2" y="7" rx="2" ry="2"/><polyline points="17 2 12 7 7 2"/></svg>
                    ${escapeHtml(info.title)} (TV Show)
                </div>
            `;
        } else if (type === 'user') {
            contextTitle.textContent = `Client Profile: User #${info.userId} (Highly Rated Movies)`;
            
            if (info.liked && info.liked.length > 0) {
                info.liked.forEach(movie => {
                    const ratingText = movie.rating ? ` (${movie.rating}★)` : '';
                    const chip = document.createElement('div');
                    chip.className = 'context-chip';
                    chip.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                        Liked: ${escapeHtml(movie.title)}${ratingText}
                    `;
                    contextHistory.appendChild(chip);
                });
            } else {
                contextHistory.innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">No rating history found in mapping subset.</span>';
            }
        }
    }

    function renderRecommendations(movies) {
        resultsGrid.innerHTML = '';
        if (!movies || movies.length === 0) {
            resultsGrid.innerHTML = `
                <div class="empty-state">
                    <h3>No Recommendations Found</h3>
                    <p>Try searching for a different title or select another client ID.</p>
                </div>
            `;
            return;
        }

        movies.forEach((movie, index) => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.style.animation = `fadeIn 0.4s ease forwards ${index * 0.05}s`;
            card.style.opacity = '0'; // For smooth fade-in animation

            const matchPercent = Math.round(movie.similarity * 100);
            const ratingVal = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
            const genresHtml = movie.parsed_genres ? movie.parsed_genres.map(g => `<span class="genre-badge">${escapeHtml(g)}</span>`).join('') : '';
            
            // For TV shows, we don't have director and cast, but we have release_date (year) and vote_count.
            // We use standard check: if director is blank, render TV shows metadata style.
            let footerMetaHtml = '';
            if (movie.director) {
                const actors = movie.parsed_cast ? movie.parsed_cast.slice(0, 3).join(', ') : 'Unknown';
                footerMetaHtml = `
                    <div class="movie-credits">
                        <div>Dir: <strong>${escapeHtml(movie.director)}</strong></div>
                        <div style="margin-top: 2px;">Cast: <strong>${escapeHtml(actors)}</strong></div>
                    </div>
                `;
            } else {
                footerMetaHtml = `
                    <div class="movie-credits">
                        <div>Year: <strong>${escapeHtml(movie.release_date || 'N/A')}</strong></div>
                        <div style="margin-top: 2px;">Votes: <strong>${movie.vote_count ? movie.vote_count.toLocaleString() : 'N/A'}</strong></div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div>
                    <div class="card-header">
                        <h3 class="movie-title">${escapeHtml(movie.title)}</h3>
                        <span class="match-badge">${matchPercent}% Match</span>
                    </div>
                    <div class="movie-genres">
                        ${genresHtml}
                    </div>
                    <p class="movie-overview">${escapeHtml(movie.overview || 'No synopsis available.')}</p>
                </div>
                <div class="card-footer">
                    ${footerMetaHtml}
                    <div class="movie-rating">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" class="rating-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                        <span>${ratingVal}</span>
                    </div>
                </div>
            `;

            resultsGrid.appendChild(card);
        });
    }

    function renderError(message) {
        resultsGrid.innerHTML = `
            <div class="empty-state" style="border-color: rgba(239, 68, 68, 0.2);">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
                <h3 style="color: #fca5a5;">Recommendation Error</h3>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
