// const submit = document.getElementById('submit_button');
// const output_result = document.getElementById('Output_results');

// submit.addEventListener('click', () => {
//     output_result.style.visibility = "visible";
// });
// const form = document.getElementById('crop-form');
//     const output = document.getElementById('Output_results');

//     form.addEventListener('submit', async (e) => {
//       e.preventDefault();                     // stop normal POST
//       const formData = new FormData(form);    // grab all inputs

//       // call your FastAPI endpoint
//       const resp = await fetch('/', {
//         method: 'POST',
//         body: formData
//       });

//       if (!resp.ok) {
//         output.innerHTML = `<p style="color:red">Error ${resp.status}</p>`;
//         return;
//       }

//       const { prediction } = await resp.json();
//       output.innerHTML = `
//         <p>It would be wise to plant <strong>${prediction}</strong>.</p>
//       `;
//     });