    $("#data").on("change", function() {
        var dataSelezionata = $(this).val();

        // Invia la richiesta AJAX all'endpoint Flask
        $.ajax({
            url: "{{ url_for('orari_disponibili') }}", // Endpoint Flask
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ "data": dataSelezionata }),
            success: function(response) {
                // Pulisci gli orari attuali
                $("#orari-container").empty();

                // Aggiungi gli orari disponibili
                response.forEach(function(orario) {
                    /*
                    $("#orari-container").append(
                        `<input type="radio" class="btn-check" name="orario" id="orario${orario.id}" value="${orario.id}" autocomplete="off">
                         <label class="btn btn-outline-primary" for="orario${orario.id}">${orario.orario}</label>`
                    );*/
                });
            },
            error: function() {
                console.log("Errore durante il recupero degli orari disponibili.");
            }
        });
    });
