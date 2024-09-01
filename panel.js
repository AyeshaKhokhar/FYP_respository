$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
        $('#content').toggleClass('active');
    });
});

$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
        $('#content').toggleClass('active');
    });

    $('.components li a').on('click', function () {
        $('.components li').removeClass('active');
        $(this).parent().addClass('active');
    });
});

function showContent(sectionId) {
    $('.content-section').removeClass('active');
    $('#' + sectionId).addClass('active');
}

// panel.js
$(document).ready(function() {
    const hotels = {
        'Hotel Sunshine': {
            name: 'Hotel Sunshine',
            owner: 'John Doe',
            email: 'john@example.com',
            address: '123 Sunshine St, Sunshine City',
            description: 'A beautiful hotel with sunny vibes.',
            image: 'hotel_sunshine.jpg',
            rooms: ['Suite', 'Deluxe Room', 'Standard Room']
        },
        'Mountain Retreat': {
            name: 'Mountain Retreat',
            owner: 'Jane Smith',
            email: 'jane@example.com',
            address: '456 Mountain Rd, Mountain City',
            description: 'A serene retreat in the mountains.',
            image: 'mountain_retreat.jpg',
            rooms: ['Mountain View Room', 'Standard Room']
        }
        
        // Add more hotels as needed
    };

    function displayAllHotels() {
        $('#all-hotels').empty();
        for (const hotelName in hotels) {
            const hotel = hotels[hotelName];
            $('#all-hotels').append(`
                <div class="detail-box">
                    <h4>${hotel.name}</h4>
                    <img src="${hotel.image}" alt="${hotel.name}">
                    <p><strong>Owner:</strong> ${hotel.owner}</p>
                    <p><strong>Email:</strong> ${hotel.email}</p>
                    <p><strong>Address:</strong> ${hotel.address}</p>
                    <p><strong>Description:</strong> ${hotel.description}</p>
                    <button class="update-btn">Update Details</button>
                    <button class="delete-btn">Delete Hotel</button>
                </div>
            `);
        }
    }

    displayAllHotels();

    $('#hotel-dropdown').on('change', function() {
        const hotelName = $(this).val();
        if (hotelName) {
            $('#all-hotels').hide();
            loadHotelDetails(hotelName);
        } else {
            $('#all-hotels').show();
            $('#selected-hotel').hide();
        }
    });

    function loadHotelDetails(hotelName) {
        const hotel = hotels[hotelName];
        if (hotel) {
            $('#selected-hotel').html(`
                <div class="detail-box">
                    <h4>${hotel.name}</h4>
                    <img src="${hotel.image}" alt="${hotel.name}">
                    <p><strong>Owner Name:</strong> ${hotel.owner}</p>
                    <p><strong>Email:</strong> ${hotel.email}</p>
                    <p><strong>Address:</strong> ${hotel.address}</p>
                    <p><strong>Description:</strong> ${hotel.description}</p>
                    <h5>Rooms:</h5>
                    <ul>${hotel.rooms.map(room => `<li>${room}</li>`).join('')}</ul>
                    <button class="update-btn">Update Details</button>
                    <button class="delete-btn">Delete Hotel</button>
                </div>
            `).show();
        } else {
            $('#selected-hotel').html('<p>No hotel selected.</p>').show();
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('edit-hotel-modal');
    var closeButton = document.querySelector('.close-button');
    var addImageButton = document.getElementById('add-image-btn');
    var imageUploadsContainer = document.getElementById('image-uploads');

    // Function to open the modal and populate it with data
    function editHotel(button) {
        var row = button.closest('tr');
        var hotelName = row.cells[0].innerText;
        var email = row.cells[1].innerText;
        var location = row.cells[2].innerText;
        var ranking = row.cells[3].innerText;

        document.getElementById('hotel-name').value = hotelName;
        document.getElementById('hotel-description').value = 'Sample description for ' + hotelName;
        document.getElementById('hotel-location').value = location;

        // Clear existing image uploads
        imageUploadsContainer.innerHTML = `
            <div class="image-upload">
                <label for="hotel-images">Hotel Images (optional)</label>
                <input type="file" id="hotel-images" name="hotel-images[]" multiple>
                <label for="image-position">Image Position</label>
                <select id="image-position" name="image-position[]">
                    <option value="">Select Image Position</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                    <option value="6">6</option>
                    <option value="7">7</option>
                </select>
            </div>
        `;

        modal.style.display = 'block';
    }

    function closeModal() {
        modal.style.display = 'none';
    }

    closeButton.addEventListener('click', closeModal);

    document.querySelectorAll('.update-btn').forEach(button => {
        button.addEventListener('click', () => editHotel(button));
    });

    document.getElementById('hotel-form').addEventListener('submit', function(e) {
        e.preventDefault();
        // Handle form submission logic here
        var formData = new FormData(this);

        // Log form data (for demonstration purposes)
        for (var [key, value] of formData.entries()) {
            console.log(key, value);
        }

        alert('Hotel information updated successfully!');
        closeModal();
    });

    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal();
        }
    }

    // Add more image input fields
    addImageButton.addEventListener('click', function() {
        var imageUploadHTML = `
            <div class="image-upload">
                <label for="hotel-images">Hotel Images (optional)</label>
                <input type="file" id="hotel-images" name="hotel-images[]" multiple>
                <label for="image-position">Image Position</label>
                <select id="image-position" name="image-position[]">
                    <option value="">Select Image Position</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                    <option value="6">6</option>
                    <option value="7">7</option>
                </select>
            </div>
        `;
        imageUploadsContainer.insertAdjacentHTML('beforeend', imageUploadHTML);
    });
});

function addRoom() {
    const roomsContainer = document.getElementById('rooms-container');
    const newRoomDiv = document.createElement('div');
    newRoomDiv.classList.add('room-group');
    newRoomDiv.innerHTML = `
        <h4>Enter another Room Details</h4>
        <label for="totalRooms">Room Name</label>
        <input type="text" name="totalRooms[]" placeholder="Enter Room name" required>
        <label for="roomPrice">Room Price<span class="required-star">*</span></label>
        <input type="number" name="roomPrice[]" placeholder="Room price" required>
        <label for="bedSize">Bed Size <span class="required-star">*</span></label>
        <select name="bedSize" required>
            <option value="single">Single Bed</option>
            <option value="double">Double Bed</option>
            <option value="extra-large">Extra Large Bed</option>
        </select>
        <label>Room Facilities <span class="required-star">*</span></label>
        <div class="checkbox-group">
            <label><input type="checkbox" name="roomFacilities" value="wifi"> WiFi</label>
            <label><input type="checkbox" name="roomFacilities" value="parking"> Parking</label>
            <label><input type="checkbox" name="roomFacilities" value="pool"> Pool</label>
            <label><input type="checkbox" name="roomFacilities" value="gym"> Gym</label>
            <label><input type="checkbox" name="roomFacilities" value="spa"> Spa</label>
            <label><input type="checkbox" name="roomFacilities" value="restaurant"> Restaurant</label>
        </div>
        <label for="roomDetails">Room Details </label>
        <textarea name="roomDetails[]" rows="4" placeholder="Enter room description" required></textarea>
        <!-- Delete Room Button -->
        <button type="button" class="deleteRoomButton">Delete Room</button>
    `;

    // Append the new roomDiv to the roomsContainer
    roomsContainer.appendChild(newRoomDiv);

    // Attach event listener to the Delete Room button
    const deleteRoomButton = newRoomDiv.querySelector('.deleteRoomButton');
    deleteRoomButton.addEventListener('click', function() {
        roomsContainer.removeChild(newRoomDiv);
    });
}
