import random
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.utils.translation import gettext as _
from employee.models import Employee


def filtersubordinates(request, queryset, perm=None):
    """
    This method is used to filter out subordinates queryset element.
    """
    user = request.user
    if user.has_perm(perm):
        return queryset
    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = queryset.filter(
        employee_id__employee_work_info__reporting_manager_id=manager
    )
    return queryset


def filtersubordinatesemployeemodel(request, queryset, perm=None):
    """
    This method is used to filter out subordinates queryset element.
    """
    user = request.user
    if user.has_perm(perm):
        return queryset
    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = queryset.filter(employee_work_info__reporting_manager_id=manager)
    return queryset


def is_reportingmanager(request):
    """
    This method is used to check weather the employee is reporting manager or not.
    """
    try:
        user = request.user
        return user.employee_get.reporting_manager.all().exists()
    except:
        return False


def choosesubordinates(
    request,
    form,
    perm,
):
    user = request.user
    if user.has_perm(perm):
        return form
    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = Employee.objects.filter(employee_work_info__reporting_manager_id=manager)
    form.fields["employee_id"].queryset = queryset
    return form


def choosesubordinatesemployeemodel(request, form, perm):
    user = request.user
    if user.has_perm(perm):
        return form
    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = Employee.objects.filter(employee_work_info__reporting_manager_id=manager)

    form.fields["employee_id"].queryset = queryset
    return form


orderingList = [
    {
        "id": "",
        "field": "",
        "ordering": "",
    }
]


def sortby(request, queryset, key):
    """
    This method is used to sort query set by asc or desc
    """
    global orderingList
    id = request.user.id
    # here will create dictionary object to the global orderingList if not exists,
    # if exists then method will switch corresponding object ordering.
    filtered_list = [x for x in orderingList if x["id"] == id]
    ordering = filtered_list[0] if filtered_list else None
    if ordering is None:
        ordering = {
            "id": id,
            "field": None,
            "ordering": "-",
        }
        orderingList.append(ordering)
    sortby = request.GET.get(key)
    if sortby is not None and sortby != "":
        # here will update the orderingList
        ordering["field"] = sortby
        if queryset.query.order_by == queryset.query.order_by:
            queryset = queryset.order_by(f'{ordering["ordering"]}{sortby}')
        if ordering["ordering"] == "-":
            ordering["ordering"] = ""
        else:
            ordering["ordering"] = "-"
        orderingList = [item for item in orderingList if item["id"] != id]
        orderingList.append(ordering)

    return queryset


def random_color_generator():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    if r == g or g == b or b == r:
        random_color_generator()
    return f"rgba({r}, {g}, {b} , 0.7)"


# color_palette=[]
# Function to generate distinct colors for each object
def generate_colors(num_colors):
    # Define a color palette with distinct colors
    color_palette = [
        "rgba(255, 99, 132, 1)",  # Red
        "rgba(54, 162, 235, 1)",  # Blue
        "rgba(255, 206, 86, 1)",  # Yellow
        "rgba(75, 192, 192, 1)",  # Green
        "rgba(153, 102, 255, 1)",  # Purple
        "rgba(255, 159, 64, 1)",  # Orange
    ]

    if num_colors > len(color_palette):
        for i in range(num_colors - len(color_palette)):
            color_palette.append(random_color_generator())

    colors = []
    for i in range(num_colors):
        # color=random_color_generator()
        colors.append(color_palette[i % len(color_palette)])

    return colors


def get_key_instances(model, data_dict):
    # Get all the models in the Django project
    all_models = apps.get_models()

    # Initialize a list to store related models include the function argument model as foreignkey
    related_models = []

    # Iterate through all models
    for other_model in all_models:
        # Iterate through fields of the model
        for field in other_model._meta.fields:
            # Check if the field is a ForeignKey and related to the function argument model
            if isinstance(field, ForeignKey) and field.related_model == model:
                related_models.append(other_model)
                break

    # Iterate through related models to filter instances
    for related_model in related_models:
        # Get all fields of the related model
        related_model_fields = related_model._meta.get_fields()

        # Iterate through fields to find ForeignKey fields
        for field in related_model_fields:
            if isinstance(field, ForeignKey):
                # Get the related name and field name
                related_name = field.related_query_name()
                field_name = field.name

                # Check if the related name exists in data_dict
                if related_name in data_dict:
                    # Get the related_id from data_dict
                    related_id_list = data_dict[related_name]
                    related_id = int(related_id_list[0])

                    # Filter instances based on the field and related_id
                    filtered_instance = related_model.objects.filter(
                        **{field_name: related_id}
                    ).first()

                    # Store the filtered instance back in data_dict
                    data_dict[related_name] = [str(filtered_instance)]

    # Get all the fields in the argument model
    model_fields = model._meta.get_fields()
    foreign_key_field_names = [
        field.name
        for field in model_fields
        if isinstance(field, ForeignKey or OneToOneField)
    ]
    # Create a list of field names that are present in data_dict
    present_foreign_key_field_names = [
        key for key in foreign_key_field_names if key in data_dict
    ]

    for field_name in present_foreign_key_field_names:
        try:
            # Get the integer value from data_dict for the field
            field_value = int(data_dict[field_name][0])

            # Get the related model of the ForeignKey field
            related_model = model._meta.get_field(field_name).remote_field.model

            # Get the instance of the related model using the field value
            related_instance = related_model.objects.get(id=field_value)

            # Update data_dict with the string representation of the instance
            data_dict[field_name] = [str(related_instance)]
        except (ObjectDoesNotExist, ValueError):
            pass

    # Create a list of field names that are ManyToManyField
    many_to_many_field_names = [
        field.name for field in model_fields if isinstance(field, ManyToManyField)
    ]
    # Create a list of field names that are present in data_dict for ManyToManyFields
    present_many_to_many_field_names = [
        key for key in many_to_many_field_names if key in data_dict
    ]

    for field_name in present_many_to_many_field_names:
        try:
            # Get the related model of the ManyToMany field
            related_model = model._meta.get_field(field_name).remote_field.model
            # Get a list of integer values from data_dict for the field
            field_values = [int(value) for value in data_dict[field_name]]

            # Filter instances of the related model based on the field values
            related_instances = related_model.objects.filter(id__in=field_values)

            # Update data_dict with the string representations of related instances
            data_dict[field_name] = [str(instance) for instance in related_instances]
        except (ObjectDoesNotExist, ValueError):
            pass

    nested_fields = [key for key in data_dict if "__" in key]
    for key in nested_fields:
        field_names = key.split("__")
        field_values = data_dict[key]
        if (
            field_values != ["unknown"]
            and field_values != ["true"]
            and field_values != ["false"]
        ):
            nested_instance = get_nested_instances(model, field_names, field_values)
            if nested_instance is not None:
                data_dict[key] = nested_instance

    return data_dict


def get_nested_instances(model, field_names, field_values):
    try:
        related_model = model
        for field_name in field_names:
            try:
                related_field = related_model._meta.get_field(field_name)
            except:
                pass
            try:
                related_model = related_field.remote_field.model
            except:
                pass
        field_values = [int(value) for value in field_values]
        related_instances = related_model.objects.filter(id__in=field_values)
        return [str(instance) for instance in related_instances]
    except (ObjectDoesNotExist, ValueError):
        return None
