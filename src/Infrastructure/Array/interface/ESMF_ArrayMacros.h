#if 0
! $Id: ESMF_ArrayMacros.h,v 1.20 2004/03/17 18:10:35 nscollins Exp $
!
! Earth System Modeling Framework
! Copyright 2002-2003, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the GPL.
!
!==============================================================================
!
#endif

#if 0
!------------------------------------------------------------------------------
! Declare a wrapper for a Fortran array pointer, a local variable of that type,
!  type which wraps every pointer type, and a declaration of local variables,
!  one of each wrapper type.
!------------------------------------------------------------------------------
#endif

#define ArrayTypeMacro(mname, mtypekind, mrank, mdim) \
! <Created by macro - do not edit directly > @\
      type ESMF_ArrWrap##mrank##D##mtypekind @\
        mname (ESMF_KIND_##mtypekind),dimension(mdim),pointer :: ptr##mrank##D##mtypekind @\
      end type ESMF_ArrWrap##mrank##D##mtypekind @\


#define ArrayLocalVarMacro(mname, mtypekind, mrank, mdim) \
        type(ESMF_ArrWrap##mrank##D##mtypekind) :: l##mrank##D##mtypekind


#if 0
!------------------------------------------------------------------------------
!------------------------------------------------------------------------------
! Create a new array from an unallocated Fortran array ptr and a list of counts.
! Documentation for this class of creates, then the actual macro.
!------------------------------------------------------------------------------
#endif

#define ArrayCreateByMTPtrDoc() \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
!BOP @\
! !IROUTINE: ESMF_ArrayCreate - make an ESMF array from an unallocated Fortran array pointer @\
! @\
! !INTERFACE: @\
!      ! Private name; call using ESMF_ArrayCreate()
!      function ESMF_ArrayCreateByMTPtr<rank><type><kind>(farr, counts, haloWidth, lbounds, ubounds, rc) @\
! @\
! !RETURN VALUE: @\
!      type(ESMF_Array) :: ESMF_ArrayCreateByMTPtr<rank><type><kind> @\
! @\
! !ARGUMENTS: @\
!      <type> (ESMF_KIND_<kind>), dimension(<rank>), pointer :: farr @\
!      integer, dimension(:), intent(in) :: counts @\
!      integer, intent(in), optional :: haloWidth @\
!      integer, dimension(:), intent(in), optional :: lbounds @\
!      integer, dimension(:), intent(in), optional :: ubounds @\
!      integer, intent(out), optional :: rc   @\
! @\
! !DESCRIPTION: @\
! Creates an {\tt Array} based on an unallocated (but allocatable) Fortran @\
!   array pointer.  This routine allocates memory to the array and fills in @\
!   the array object with all necessary information. @\
! @\
! The function return is an {\tt ESMF\_Array} type with space @\
! allocated for data. @\
! @\
! The arguments are: @\
!  \begin{description} @\
!  \item[farr] @\
!    An allocatable (but currently unallocated) Fortran array pointer.  @\
!  \item[counts] @\
!    An integer array of counts.  Must be the same length as the rank. @\
!  \item[{[haloWidth]}]  @\
!    An integer count of the width of the halo region on all sides of @\
!   the array. The default is 0, no halo region. @\
!  \item[{[lbounds]}]  @\
!    An integer array of lower index values.  Must be the same length @\
!    as the rank. @\
!  \item[{[ubounds]}]  @\
!    An integer array of upper index values.  Must be the same length @\
!    as the rank. @\
!  \item[{[rc]}] @\
!    Return code; equals {\tt ESMF\_SUCCESS} if there are no errors. @\
!  \end{description} @\
! @\
!EOPI @\
 @\

#define ArrayCreateByMTPtrMacro(mname, mtypekind, mrank, mdim, mlen, mloc) \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
      function ESMF_ArrayCreateByMTPtr##mrank##D##mtypekind(fptr, counts, haloWidth, & @\
                                                     lbounds, ubounds, rc) @\
 @\
      type(ESMF_Array) :: ESMF_ArrayCreateByMTPtr##mrank##D##mtypekind @\
 @\
      mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer :: fptr @\
      integer, dimension(:), intent(in) :: counts @\
      integer, intent(in), optional :: haloWidth @\
      integer, dimension(:), intent(in), optional :: lbounds @\
      integer, dimension(:), intent(in), optional :: ubounds @\
      integer, intent(out), optional :: rc   @\
 @\
        ! Local variables @\
        type (ESMF_Array) :: array          ! new array object @\
        integer :: status                   ! local error status @\
        integer :: hwidth                   ! local copy of halo width @\
        logical :: rcpresent                ! did user specify rc? @\
 @\
        ! Initialize return code; assume failure until success is certain @\
        status = ESMF_FAILURE @\
        rcpresent = .FALSE. @\
        array%this = ESMF_NULL_POINTER @\
 @\
        if (present(rc)) then @\
          rcpresent = .TRUE. @\
          rc = ESMF_FAILURE @\
        endif @\
 @\
        ! Test to see if array already allocated, and fail if so. @\
        if (associated(fptr)) then @\
          print *, "Pointer cannot already be allocated" @\
          return @\
        endif @\
 @\
        ! Always supply a halo value, setting it to 0 if not specified. @\
        if (present(haloWidth)) then @\
          hwidth = haloWidth @\
        else @\
          hwidth = 0 @\
        endif @\
 @\
        ! Call create routine @\
        call c_ESMC_ArrayCreateNoData(array, mrank, ESMF_DATA_##mname, ESMF_##mtypekind, & @\
                                          ESMF_FROM_FORTRAN, status) @\
        if (status .ne. ESMF_SUCCESS) then @\
          print *, "Array initial construction error" @\
          return @\
        endif @\
 @\
        call ESMF_ArrayConstructF90Ptr##mrank##D##mtypekind(array, counts, hwidth,& @\
                                 fptr, ESMF_DATA_SPACE, lbounds, ubounds, status) @\
 @\
        ! return value set by c_ESMC func above @\
        ESMF_ArrayCreateByMTPtr##mrank##D##mtypekind = array @\
        if (rcpresent) rc = status @\
 @\
        end function ESMF_ArrayCreateByMTPtr##mrank##D##mtypekind   @\
 @\
! < end macro - do not edit directly >  @\
!------------------------------------------------------------------------------ @\


#if 0
!------------------------------------------------------------------------------
!------------------------------------------------------------------------------
! Create a new array based on an allocated Fortran array and a copy flag.
! Documentation for this class of creates, then the actual macro.
!------------------------------------------------------------------------------
#endif

#define ArrayCreateByFullPtrDoc() \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
!BOP @\
! !IROUTINE: ESMF_ArrayCreate - make an ESMF array from an allocated Fortran array @\
! @\
! !INTERFACE: @\
!     ! Private name; call using ESMF_ArrayCreate()
!      function ESMF_ArrayCreateByFullPtr<rank><type><kind>(farr, docopy, haloWidth, rc) @\
! @\
! !RETURN VALUE: @\
!      type(ESMF_Array) :: ESMF_ArrayCreateByFullPtr<rank><type><kind> @\
! @\
! !ARGUMENTS: @\
!      <type> (ESMF_KIND_<kind>), dimension(<rank>), pointer :: farr @\
!      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
!      integer, intent(in), optional :: haloWidth @\
!      integer, intent(out), optional :: rc   @\
! @\
! !DESCRIPTION: @\
! Creates an {\tt Array} based on an already allocated Fortran array @\ 
!   pointer.  This routine can make a copy or reference the existing data @\
!   and fills in the array object with all necessary information. @\
! @\
! The function return is an {\tt ESMF\_Array} type. @\
! @\
! The arguments are: @\
!  \begin{description} @\
!  \item[farr] @\
!    An allocated Fortran array pointer. @\
!  \item[{[docopy]}] @\
!   Default to {\tt ESMF\_DATA\_REF}, makes the {\tt ESMF\_Array} reference @\
!   the existing data array.  If set to {\tt ESMF\_DATA\_COPY} this routine @\
!   allocates new space and copies the data from the pointer @\
!   into the new array. @\
!  \item[{[haloWidth]}] @\
!    Set the maximum width of the halo region on all edges. Defaults to 0. @\
!  \item[{[rc]}] @\
!    Return code; equals {\tt ESMF\_SUCCESS} if there are no errors. @\
!  \end{description} @\
! @\
!EOP @\
 @\


#define ArrayCreateByFullPtrMacro(mname, mtypekind, mrank, mdim, mlen, mloc) \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
 @\
      function ESMF_ArrayCreateByFullPtr##mrank##D##mtypekind(fptr, docopy, haloWidth, rc) @\
 @\
      type(ESMF_Array) :: ESMF_ArrayCreateByFullPtr##mrank##D##mtypekind @\
 @\
      mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer :: fptr @\
      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
      integer, intent(in), optional :: haloWidth @\
      integer, intent(out), optional :: rc   @\
 @\
        ! Local variables @\
        type (ESMF_Array) :: array          ! new array object @\
        integer :: status                   ! local error status @\
        integer :: hwidth                   ! local copy of halo width @\
        logical :: rcpresent                ! did user specify rc? @\
        type (ESMF_CopyFlag) :: copy        ! do we copy or ref? @\
        integer, dimension(mrank) :: counts ! per dim @\
        integer, dimension(mrank) :: lbounds ! per dim @\
        integer, dimension(mrank) :: ubounds ! per dim @\
 @\
        ! Initialize return code; assume failure until success is certain @\
        status = ESMF_FAILURE @\
        rcpresent = .FALSE. @\
        array%this = ESMF_NULL_POINTER @\
 @\
        if (present(rc)) then @\
          rcpresent = .TRUE. @\
          rc = ESMF_FAILURE @\
        endif @\
 @\
        ! Set default for copyflag @\
        if (present(docopy)) then @\
            copy = docopy @\
        else @\
            copy = ESMF_DATA_REF @\
        endif @\
 @\
        ! Test to see if array is not already allocated, and fail if so. @\
        if (.not.associated(fptr)) then @\
          print *, "Pointer must already be associated" @\
          return @\
        endif @\
 @\
        ! Get sizes from current array, although the construct routine @\
        !   does not need it for an already allocated array.  @\
        counts = shape(fptr) @\
        lbounds = lbound(fptr) @\
        ubounds = ubound(fptr) @\
 @\
        ! Always supply a halo value, setting it to 0 if not specified. @\
        if (present(haloWidth)) then @\
          hwidth = haloWidth @\
        else @\
          hwidth = 0 @\
        endif @\
 @\
        ! Call create routine @\
        call c_ESMC_ArrayCreateNoData(array, mrank, ESMF_DATA_##mname, ESMF_##mtypekind, & @\
                                      ESMF_FROM_FORTRAN, status) @\
        if (status .ne. ESMF_SUCCESS) then @\
          print *, "Array initial construction error" @\
          return @\
        endif @\
 @\
        call ESMF_ArrayConstructF90Ptr##mrank##D##mtypekind(array, counts, hwidth,& @\
                                  fptr, copy, lbounds, ubounds, status) @\
 @\
        ! return value set by c_ESMC func above @\
        ESMF_ArrayCreateByFullPtr##mrank##D##mtypekind = array @\
        if (rcpresent) rc = status @\
 @\
        end function ESMF_ArrayCreateByFullPtr##mrank##D##mtypekind   @\
 @\
! < end macro - do not edit directly >  @\
!------------------------------------------------------------------------------ @\

#if 0
!------------------------------------------------------------------------------
!------------------------------------------------------------------------------
! Create a Fortran pointer of the proper type and set the corresponding values
!  in the array object.  The doc and then actual macro.
!------------------------------------------------------------------------------
#endif

#define ArrayConstructF90PtrDoc() \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
!BOPI @\
! !IROUTINE: ESMF_ArrayConstructF90Ptr - Create a Fortran Pointer of the proper T/K/R @\
! @\
! !INTERFACE: @\
!      subroutine ESMF_ArrayConstructF90Ptr<rank><type><kind>(array, counts, hwidth, fptr, & @\
!                                                   docopy, lbounds, ubounds, rc) @\
! @\
! !ARGUMENTS: @\
!      type(ESMF_Array), intent(inout) :: array @\
!      integer, dimension(:), intent(in) :: counts @\
!      integer, intent(in) :: hwidth @\
!      <type> (ESMF_KIND_<kind>), dimension(<rank>), pointer, optional :: fptr  @\
!      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
!      integer, dimension(:), intent(in), optional :: lbounds @\
!      integer, dimension(:), intent(in), optional :: ubounds @\
!      integer, intent(out), optional :: rc   @\
! @\
! !DESCRIPTION: @\
!  Creates a Fortran pointer of the requested T/K/R.  After creating the @\
!  pointer and doing the allocation based on counts, also goes ahead and @\
!  calls into the C++ interfaces to set values on the {\tt ESMF\_Array} @\
!  object. (This is to save on the total number of nested crossings of the @\
!  Fortran/C++ boundary.) @\
! @\
!  Optional args are an existing Fortran pointer which if given is used @\
!  instead of a new one, and a docopy flag which if set to copy will @\
!  do a contents copy or reference. @\
! The arguments are: @\
!  \begin{description} @\
!  \item[array]  The {\tt ESMF\_Array} to set the values into. @\
!  \item[counts]  An integer array of counts.  Must be the same length as the rank. @\
!  \item[hwidth]  An integer halo width. Width on each edge. @\
!  \item[{[fptr]}] An optional existing Fortran pointer.  Will be used instead of an @\
!   internally generated Fortran pointer if given.  Must be given if the {\tt docopy} is specified. @\
!  \item[{[docopy]}]  An optional copy flag which can be specified if an Fortran pointer is also @\
!   given.  Can either make a new copy of the data or ref existing data. @\
!  \item[{[lbounds]}]  An integer array of lower index values.  Must be the same length as the rank. @\
!  \item[{[ubounds]}]  An integer array of upper index values.  Must be the same length as the rank. @\
!  \item[{[rc]}]  Return code; equals {\tt ESMF\_SUCCESS} if there are no errors. @\
!  \end{description} @\
! @\
!EOPI @\
 @\

#define ArrayConstructF90PtrMacro(mname, mtypekind, mrank, mdim, mlen, mrng, mloc) \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly > @\
      subroutine ESMF_ArrayConstructF90Ptr##mrank##D##mtypekind(array, counts, hwidth, fptr, & @\
                                                   docopy, lbounds, ubounds, rc) @\
 @\
      type(ESMF_Array), intent(inout) :: array @\
      integer, dimension(:), intent(in) :: counts @\
      integer, intent(in) :: hwidth @\
      mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer, optional :: fptr  @\
      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
      integer, dimension(:), intent(in), optional :: lbounds @\
      integer, dimension(:), intent(in), optional :: ubounds @\
      integer, intent(out), optional :: rc   @\
 @\
        ! Local variables @\
        integer :: i                        ! temp var @\
        integer :: status                   ! local error status @\
        logical :: rcpresent                ! did user specify rc? @\
        logical :: willalloc                ! do we need to alloc/dealloc? @\
        logical :: willcopy                 ! do we need to copy data? @\
        type(ESMF_Logical) :: do_dealloc    ! dealloc flag for SetInfo call @\
 @\
        type (ESMF_ArrWrap##mrank##D##mtypekind) :: wrap ! to pass f90 ptr to C++ @\
        mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer :: newp  @\
        integer, dimension(ESMF_MAXDIM) :: lb, ub @\
        integer, dimension(ESMF_MAXDIM) :: offsets @\
 @\
        ! Initialize return code; assume failure until success is certain @\
        status = ESMF_FAILURE @\
        rcpresent = .FALSE. @\
        if (present(rc)) then @\
          rcpresent = .TRUE. @\
          rc = ESMF_FAILURE @\
        endif @\
 @\
        ! Assume defaults first, then alter if lb or ub specified, @\
        ! or if an existing pointer is given and can be queried. @\
        lb(:) = 1 @\
        ub(1:size(counts)) = counts @\
 @\
        ! Decide if we need to do: make a new allocation, copy existing data @\
        if (.not. present(fptr)) then @\
           nullify(newp) @\
           willalloc = .true. @\
           willcopy = .false. @\
           do_dealloc = ESMF_TRUE @\
        else @\
           if (docopy .eq. ESMF_DATA_SPACE) then @\
               newp => fptr    ! ptr alias, important this be =>  @\
               lb(1:size(counts)) = lbound(fptr) @\
               ub(1:size(counts)) = ubound(fptr) @\
               willalloc = .true. @\
               willcopy = .false. @\
               do_dealloc = ESMF_TRUE @\
           else if (docopy .eq. ESMF_DATA_COPY) then @\
               nullify(newp) @\
               willalloc = .true. @\
               willcopy = .true. @\
               do_dealloc = ESMF_TRUE @\
           else       ! ESMF_DATA_REF @\
               newp => fptr    ! ptr alias, important this be =>  @\
               lb(1:size(counts)) = lbound(fptr) @\
               ub(1:size(counts)) = ubound(fptr) @\
               willalloc = .false. @\
               willcopy = .false. @\
               do_dealloc = ESMF_FALSE @\
           endif @\
        endif @\
 @\
        ! lbounds, if given, should be used @\
        if (present(lbounds)) then @\
            lb(1:size(lbounds)) = lbounds @\
        endif @\
 @\
        ! ub is only used during allocation @\
        if (willalloc) then @\
            if (present(ubounds)) then @\
                ub(1:size(ubounds)) = ubounds @\
            endif @\
            allocate(newp ( mrng ), stat=status) @\
            if (status .ne. 0) then     ! f90 status, not ESMF @\
              print *, "Array space allocate error" @\
              return @\
            endif @\
        endif @\
 @\
        if (willcopy) then @\
            newp = fptr      ! contents copy, important that this be = @\
        endif @\
 @\
        ! Now set all the new accumulated information about the array - the @\
        ! F90 pointer, the base addr, the counts, etc. @\
 @\
	! Until we need to use byte offsets, leave them 0. @\
        offsets = 0 @\
 @\
        wrap % ptr##mrank##D##mtypekind => newp @\
        call c_ESMC_ArraySetInfo(array, wrap, & @\
                                 ESMF_DATA_ADDRESS(newp(mloc)), counts, & @\
                                 lb, ub, offsets, & @\
                                 ESMF_TRUE, do_dealloc, hwidth, status) @\
 @\
        if (status .ne. ESMF_SUCCESS) then @\
          print *, "Array internal set info error" @\
          return @\
        endif @\
 @\
        if (rcpresent) rc = status @\
 @\
        end subroutine ESMF_ArrayConstructF90Ptr##mrank##D##mtypekind  @\
 @\
! < end macro - do not edit directly >  @\
!------------------------------------------------------------------------------ @\

#if 0
!------------------------------------------------------------------------------
!------------------------------------------------------------------------------
! Get a Fortran pointer to the data contained in this array
!------------------------------------------------------------------------------
#endif

#define ArrayGetDataDoc() \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly >  @\
!BOPI @\
! !INTERFACE: @\
!      subroutine ESMF_ArrayGetData<rank><type><kind>(array, fptr, docopy, rc) @\
! @\
! !ARGUMENTS: @\
!      type(ESMF_Array) :: array @\
!      <type> (ESMF_KIND_<kind>), dimension(<rank>), pointer :: fptr @\
!      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
!      integer, intent(out), optional :: rc @\
! @\
! !DESCRIPTION: @\
!      Return a Fortran pointer to the existing data buffer, @\
!      or return a Fortran pointer to a new copy of the data. @\
! @\
! The arguments are: @\
!  \begin{description} @\
!  \item[array] @\
!    An {\tt ESMF\_Array} type.
!  \item[farr] @\
!    An allocatable (but currently unallocated) Fortran array pointer.  @\
!  \item[docopy] @\
!   Default to {\tt ESMF\_DATA\_REF}, makes the {\tt ESMF\_Array} reference @\
!   the existing data array.  If set to {\tt ESMF\_DATA\_COPY} this routine @\
!   allocates new space and copies the data from the pointer into the space. @\
!  \item[{[rc]}] @\
!    Return code; equals {\tt ESMF\_SUCCESS} if there are no errors. @\
!  \end{description} @\
! @\
!EOPI @\
 @\

#define ArrayGetDataMacro(mname, mtypekind, mrank, mdim, mlen, mrng, mloc) \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly >  @\
      subroutine ESMF_ArrayGetData##mrank##D##mtypekind(array, fptr, docopy, rc) @\
 @\
      type(ESMF_Array) :: array @\
      mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer :: fptr @\
      type(ESMF_CopyFlag), intent(in), optional :: docopy @\
      integer, intent(out), optional :: rc @\
 @\
        integer :: status                   ! local error status @\
        logical :: rcpresent                ! did user specify rc? @\
        logical :: copyreq                  ! did user specify copy? @\
 @\
        type (ESMF_ArrWrap##mrank##D##mtypekind) :: wrap     ! for passing f90 ptr to C++ @\
        integer :: rank, lb(mrank), ub(mrank)  ! size info for the array @\
        mname (ESMF_KIND_##mtypekind), dimension(mdim), pointer :: localp ! local copy @\
 @\
        ! initialize return code; assume failure until success is certain @\
        status = ESMF_FAILURE @\
        rcpresent = .FALSE. @\
        if (present(rc)) then @\
          rcpresent = .TRUE. @\
          rc = ESMF_FAILURE @\
        endif @\
 @\
        copyreq = .FALSE. @\
 @\
        ! check copyflag to see if we are making a reference @\
        ! or making a new array and a copy @\
        if (present(docopy)) then @\
          if (docopy .eq. ESMF_DATA_COPY) copyreq = .TRUE. @\
        endif @\
 @\
        call c_ESMC_ArrayGetF90Ptr(array, wrap, status) @\
        if (status .ne. ESMF_SUCCESS) then @\
          print *, "Array - get pointer error" @\
          return @\
        endif @\
 @\
        ! Allocate a new buffer if requested and return a copy @\
        if (copyreq) then @\
          call c_ESMC_ArrayGetLbounds(array, mrank, lb, status) @\
          if (status .ne. ESMF_SUCCESS) then @\
            print *, "Array - cannot retrieve array dim sizes" @\
            return @\
          endif @\
          call c_ESMC_ArrayGetUbounds(array, mrank, ub, status) @\
          if (status .ne. ESMF_SUCCESS) then @\
            print *, "Array - cannot retrieve array dim sizes" @\
            return @\
          endif @\
          allocate(localp( mrng ), stat=status) @\
          if (status .ne. 0) then     ! f90 status, not ESMF @\
            print *, "Array do_copy allocate error" @\
            return @\
          endif @\
          ! this must do a contents assignment @\
          localp = wrap % ptr##mrank##D##mtypekind @\
          fptr => localp  @\
        else @\
          fptr => wrap % ptr##mrank##D##mtypekind @\
        endif @\
 @\
        if (rcpresent) rc = ESMF_SUCCESS @\
 @\
        end subroutine ESMF_ArrayGetData##mrank##D##mtypekind @\
 @\
! < end macro - do not edit directly >  @\
!------------------------------------------------------------------------------ @\

#if 0
!------------------------------------------------------------------------------
!------------------------------------------------------------------------------
! Deallocate the contents of the array.
!------------------------------------------------------------------------------
#endif

#define ArrayDeallocateDoc() \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly >  @\
!BOPI @\
! !INTERFACE: @\
!      subroutine ESMF_ArrayDeallocate<rank><type><kind>(array, wrap, rc) @\
! @\
! !ARGUMENTS: @\
!      type(ESMF_Array) :: array @\
!      type (ESMF_ArrWrap<rank><type><kind>) :: wrap @\
!      integer, intent(out), optional :: rc @\
! @\
! !DESCRIPTION: @\
!      Deallocate data contents if Array object is responsible for cleaning up. @\
! @\
!EOPI @\
 @\

#define ArrayDeallocateMacro(mname, mtypekind, mrank, mdim, mlen, mloc) \
!------------------------------------------------------------------------------ @\
! <Created by macro - do not edit directly >  @\
      subroutine ESMF_ArrayDeallocate##mrank##D##mtypekind(array, wrap, rc) @\
 @\
      type(ESMF_Array) :: array @\
      type (ESMF_ArrWrap##mrank##D##mtypekind) :: wrap @\
      integer, intent(out), optional :: rc @\
 @\
        integer :: status                               ! local error status @\
 @\
        status = ESMF_FAILURE  @\
 @\
        call c_ESMC_ArrayGetF90Ptr(array, wrap, status) @\
        deallocate(wrap % ptr##mrank##D##mtypekind) @\
 @\
        if (present(rc)) rc = status @\
 @\
        end subroutine ESMF_ArrayDeallocate##mrank##D##mtypekind @\
 @\
! < end macro - do not edit directly >  @\
!------------------------------------------------------------------------------ @\

